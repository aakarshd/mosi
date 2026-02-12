"""Layer 3 Technical Rules Engine — event-driven rule evaluation.

Subscribes to broker price feed, maintains per-stock technical state,
computes indicators on each tick, and evaluates user rules to generate signals.
Active only during market hours (9:15-15:30 IST).
"""

import logging
from dataclasses import dataclass

from app.services.technical.broker_feed import BrokerFeed
from app.services.technical.state import StockTechnicalState, PositionState, OHLCV, detect_consolidation
from app.services.technical.indicators import (
    compute_macd, compute_rsi, detect_breakout, compute_levels, compute_trendline, compute_volume_ratio,
)
from app.services.technical.rules import evaluate_entry, evaluate_exit, check_addition_cap
from app.utils.datetime_helpers import market_hours_active

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Signal output consumed by the Readiness Engine."""
    user_id: str
    symbol: str
    signal_type: str  # "entry" or "exit"
    rule_name: str
    triggered: bool
    reasons: list[str]
    indicator_snapshot: dict


class TechnicalEngine:
    """Event-driven technical analysis and rule evaluation engine."""

    def __init__(self, broker_feed: BrokerFeed):
        self.feed = broker_feed
        self._stock_states: dict[str, StockTechnicalState] = {}
        self._position_states: dict[str, dict[str, PositionState]] = {}  # {user_id: {symbol: state}}
        self._user_rules: dict[str, dict] = {}  # {user_id: {entry_rule, exit_rule, addition_cap}}
        self._signal_callbacks: list = []

    def register_signal_callback(self, callback) -> None:
        """Register a callback to receive signals."""
        self._signal_callbacks.append(callback)

    def set_user_rules(self, user_id: str, rules: dict) -> None:
        """Set a user's trading rules configuration."""
        self._user_rules[user_id] = rules

    def set_position(self, user_id: str, position: PositionState) -> None:
        """Register a user's open position for exit rule tracking."""
        if user_id not in self._position_states:
            self._position_states[user_id] = {}
        self._position_states[user_id][position.symbol] = position

    async def start(self, symbols: list[str]) -> None:
        """Start the engine — subscribe to price feeds and begin rule evaluation."""
        logger.info(f"Starting technical engine for {len(symbols)} symbols")

        # Seed historical state
        for symbol in symbols:
            try:
                historical = await self.feed.get_historical_ohlcv(symbol)
                state = StockTechnicalState(symbol=symbol)
                for bar in historical:
                    state.update(bar)
                self._stock_states[symbol] = state
                logger.info(f"Seeded {symbol} with {len(historical)} bars")
            except NotImplementedError:
                self._stock_states[symbol] = StockTechnicalState(symbol=symbol)
                logger.warning(f"No historical data for {symbol} — starting fresh")

        # Subscribe to live feed
        await self.feed.subscribe(symbols, self._on_tick)

    async def stop(self) -> None:
        """Stop the engine."""
        await self.feed.disconnect()
        logger.info("Technical engine stopped")

    async def _on_tick(self, symbol: str, bar: OHLCV) -> None:
        """Handle incoming price tick — compute indicators and evaluate rules."""
        if not market_hours_active():
            return

        state = self._stock_states.get(symbol)
        if state is None:
            state = StockTechnicalState(symbol=symbol)
            self._stock_states[symbol] = state

        state.update(bar)

        # Compute indicators
        macd = compute_macd(state.closes)
        rsi = compute_rsi(state.closes)
        sr_levels = compute_levels(state.highs, state.lows, state.closes)
        resistance = sr_levels.resistance if sr_levels else 0
        breakout = detect_breakout(state.closes, state.volumes, resistance)
        trendline = compute_trendline(state.lows)
        vol_ratio = compute_volume_ratio(state.volumes)
        in_consolidation = detect_consolidation(state.closes)

        indicator_snapshot = {
            "macd": {"line": macd.macd_line, "signal": macd.signal_line, "histogram": macd.histogram} if macd else None,
            "rsi": rsi,
            "support_resistance": {"support": sr_levels.support, "resistance": sr_levels.resistance} if sr_levels else None,
            "volume_ratio": vol_ratio,
            "in_consolidation": in_consolidation,
        }

        # Evaluate rules for each user
        for user_id, rules in self._user_rules.items():
            # Entry signals (for stocks not yet in position)
            positions = self._position_states.get(user_id, {})
            if symbol not in positions:
                entry_signal = evaluate_entry(
                    rules.get("entry_rule", "breakout_volume_macd"),
                    macd, breakout, vol_ratio, in_consolidation,
                )
                if entry_signal.triggered:
                    await self._emit_signal(Signal(
                        user_id=user_id, symbol=symbol, signal_type="entry",
                        rule_name=entry_signal.rule_name, triggered=True,
                        reasons=entry_signal.reasons, indicator_snapshot=indicator_snapshot,
                    ))
            else:
                # Exit signals (for held positions)
                position = positions[symbol]
                position.update_high(bar.close)

                exit_signal = evaluate_exit(
                    rules.get("exit_rule", "eight_pct_drop"),
                    bar.close, position.post_entry_high, macd, trendline,
                )
                if exit_signal.triggered:
                    await self._emit_signal(Signal(
                        user_id=user_id, symbol=symbol, signal_type="exit",
                        rule_name=exit_signal.rule_name, triggered=True,
                        reasons=exit_signal.reasons, indicator_snapshot=indicator_snapshot,
                    ))

    async def _emit_signal(self, signal: Signal) -> None:
        """Emit signal to all registered callbacks."""
        logger.info(f"Signal: {signal.signal_type} for {signal.symbol} (user: {signal.user_id})")
        for callback in self._signal_callbacks:
            try:
                await callback(signal)
            except Exception as e:
                logger.error(f"Signal callback failed: {e}")
