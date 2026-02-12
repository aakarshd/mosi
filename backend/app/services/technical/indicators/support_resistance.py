"""Support and Resistance level computation.

Uses pivot points and swing high/low detection from price history.
"""

from dataclasses import dataclass


@dataclass
class SRLevels:
    support: float
    resistance: float
    pivot: float
    support_touches: int    # Number of times price bounced off support
    resistance_touches: int  # Number of times price tested resistance


def _find_swing_points(highs: list[float], lows: list[float], window: int = 5) -> tuple[list[float], list[float]]:
    """Find swing highs and swing lows using a rolling window."""
    swing_highs = []
    swing_lows = []

    for i in range(window, len(highs) - window):
        # Swing high: highest in its window
        if highs[i] == max(highs[i - window : i + window + 1]):
            swing_highs.append(highs[i])
        # Swing low: lowest in its window
        if lows[i] == min(lows[i - window : i + window + 1]):
            swing_lows.append(lows[i])

    return swing_highs, swing_lows


def compute_levels(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    window: int = 5,
) -> SRLevels | None:
    """Compute support/resistance from OHLC data.

    Uses pivot points from recent swing highs/lows.

    Args:
        highs: High prices (oldest first).
        lows: Low prices (oldest first).
        closes: Close prices (oldest first).
        window: Window size for swing detection.

    Returns:
        SRLevels with support, resistance, and pivot, or None if insufficient data.
    """
    min_data = window * 3
    if len(highs) < min_data or len(lows) < min_data:
        return None

    swing_highs, swing_lows = _find_swing_points(highs, lows, window)

    if not swing_highs or not swing_lows:
        # Fallback: use recent high/low
        recent = min(20, len(highs))
        resistance = max(highs[-recent:])
        support = min(lows[-recent:])
    else:
        # Use most recent swing points
        resistance = max(swing_highs[-3:]) if len(swing_highs) >= 3 else max(swing_highs)
        support = min(swing_lows[-3:]) if len(swing_lows) >= 3 else min(swing_lows)

    pivot = (resistance + support + closes[-1]) / 3

    # Count touches (price within 1% of level)
    tolerance = 0.01
    r_touches = sum(1 for h in highs[-20:] if abs(h - resistance) / resistance < tolerance)
    s_touches = sum(1 for l in lows[-20:] if abs(l - support) / support < tolerance)

    return SRLevels(
        support=support,
        resistance=resistance,
        pivot=pivot,
        support_touches=s_touches,
        resistance_touches=r_touches,
    )
