"""Entry rule evaluation — 3 user-configurable options from MOSI Algorithm.

Option 1: Breakout + Volume + MACD
  - Price breakout above resistance
  - Volume > average (1.5x)
  - MACD bullish crossover

Option 2: MACD + Consolidation + Volume
  - MACD bullish crossover
  - After consolidation phase (Bollinger squeeze / narrow range)
  - Volume spike

Option 3: Breakout + Volume (simplified)
  - Price breakout above resistance
  - Volume confirmation (1.5x average)
"""

from dataclasses import dataclass

from app.services.technical.indicators import (
    MACDResult, BreakoutSignal, compute_volume_ratio,
)


@dataclass
class EntrySignal:
    triggered: bool
    rule_name: str
    reasons: list[str]


def evaluate_entry(
    rule: str,
    macd: MACDResult | None,
    breakout: BreakoutSignal | None,
    volume_ratio: float,
    in_consolidation: bool = False,
) -> EntrySignal:
    """Evaluate entry rule for a stock.

    Args:
        rule: One of "breakout_volume_macd", "macd_consolidation_volume", "breakout_volume"
        macd: Current MACD state.
        breakout: Current breakout detection state.
        volume_ratio: Current volume / average volume.
        in_consolidation: Whether stock is in consolidation phase.

    Returns:
        EntrySignal with trigger status and reasons.
    """
    if rule == "breakout_volume_macd":
        return _rule_breakout_volume_macd(macd, breakout, volume_ratio)
    elif rule == "macd_consolidation_volume":
        return _rule_macd_consolidation_volume(macd, volume_ratio, in_consolidation)
    elif rule == "breakout_volume":
        return _rule_breakout_volume(breakout, volume_ratio)
    else:
        return EntrySignal(False, rule, [f"Unknown entry rule: {rule}"])


def _rule_breakout_volume_macd(
    macd: MACDResult | None,
    breakout: BreakoutSignal | None,
    volume_ratio: float,
) -> EntrySignal:
    reasons = []
    checks = []

    if breakout and breakout.is_breakout:
        checks.append(True)
        reasons.append(f"Breakout: price {breakout.price:.2f} above resistance {breakout.resistance_level:.2f}")
    else:
        checks.append(False)
        reasons.append("No breakout detected")

    if volume_ratio >= 1.5:
        checks.append(True)
        reasons.append(f"Volume confirmed: {volume_ratio:.1f}x average")
    else:
        checks.append(False)
        reasons.append(f"Volume insufficient: {volume_ratio:.1f}x (need 1.5x)")

    if macd and macd.bullish_crossover:
        checks.append(True)
        reasons.append("MACD bullish crossover")
    else:
        checks.append(False)
        reasons.append("No MACD bullish crossover")

    return EntrySignal(all(checks), "breakout_volume_macd", reasons)


def _rule_macd_consolidation_volume(
    macd: MACDResult | None,
    volume_ratio: float,
    in_consolidation: bool,
) -> EntrySignal:
    reasons = []
    checks = []

    if macd and macd.bullish_crossover:
        checks.append(True)
        reasons.append("MACD bullish crossover")
    else:
        checks.append(False)
        reasons.append("No MACD bullish crossover")

    if in_consolidation:
        checks.append(True)
        reasons.append("Stock was in consolidation phase")
    else:
        checks.append(False)
        reasons.append("Not in consolidation")

    if volume_ratio >= 1.5:
        checks.append(True)
        reasons.append(f"Volume spike: {volume_ratio:.1f}x average")
    else:
        checks.append(False)
        reasons.append(f"No volume spike: {volume_ratio:.1f}x")

    return EntrySignal(all(checks), "macd_consolidation_volume", reasons)


def _rule_breakout_volume(
    breakout: BreakoutSignal | None,
    volume_ratio: float,
) -> EntrySignal:
    reasons = []
    checks = []

    if breakout and breakout.is_breakout:
        checks.append(True)
        reasons.append(f"Breakout: price {breakout.price:.2f} above resistance {breakout.resistance_level:.2f}")
    else:
        checks.append(False)
        reasons.append("No breakout detected")

    if volume_ratio >= 1.5:
        checks.append(True)
        reasons.append(f"Volume confirmed: {volume_ratio:.1f}x average")
    else:
        checks.append(False)
        reasons.append(f"Volume insufficient: {volume_ratio:.1f}x")

    return EntrySignal(all(checks), "breakout_volume", reasons)
