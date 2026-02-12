"""Per-stock technical state tracking.

Maintains rolling windows for indicator computation and tracks
per-position state (post-entry high for trailing stop, consolidation phase, etc.)
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OHLCV:
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime


@dataclass
class StockTechnicalState:
    """Mutable state tracked per stock for indicator computation."""
    symbol: str
    closes: list[float] = field(default_factory=list)
    highs: list[float] = field(default_factory=list)
    lows: list[float] = field(default_factory=list)
    volumes: list[float] = field(default_factory=list)
    last_updated: datetime | None = None

    # Max rolling window (MACD needs ~50+ periods)
    MAX_WINDOW = 200

    def update(self, bar: OHLCV) -> None:
        """Add a new OHLCV bar to the state."""
        self.closes.append(bar.close)
        self.highs.append(bar.high)
        self.lows.append(bar.low)
        self.volumes.append(bar.volume)
        self.last_updated = bar.timestamp

        # Trim to max window
        if len(self.closes) > self.MAX_WINDOW:
            self.closes = self.closes[-self.MAX_WINDOW:]
            self.highs = self.highs[-self.MAX_WINDOW:]
            self.lows = self.lows[-self.MAX_WINDOW:]
            self.volumes = self.volumes[-self.MAX_WINDOW:]


@dataclass
class PositionState:
    """Per-user per-stock position state for rule evaluation."""
    user_id: str
    symbol: str
    entry_price: float
    entry_date: datetime
    quantity: int
    post_entry_high: float  # Track running high for 8% trailing stop
    total_additions: float  # Cumulative addition value

    def update_high(self, current_price: float) -> None:
        """Update post-entry high if current price exceeds it."""
        if current_price > self.post_entry_high:
            self.post_entry_high = current_price


def detect_consolidation(closes: list[float], period: int = 20, squeeze_threshold: float = 0.05) -> bool:
    """Detect if a stock is in a consolidation phase.

    Uses price range narrowing: if the range of last `period` bars is less than
    `squeeze_threshold` of the average price, the stock is consolidating.

    Args:
        closes: Recent closing prices.
        period: Lookback period.
        squeeze_threshold: Max range/avg ratio to qualify as consolidation.

    Returns:
        True if stock appears to be consolidating.
    """
    if len(closes) < period:
        return False

    recent = closes[-period:]
    high = max(recent)
    low = min(recent)
    avg = sum(recent) / len(recent)

    if avg == 0:
        return False

    range_ratio = (high - low) / avg
    return range_ratio < squeeze_threshold
