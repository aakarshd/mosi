"""Breakout detection — price above resistance with volume confirmation.

A breakout occurs when:
  1. Price closes above the computed resistance level
  2. Volume exceeds N-day average by a threshold (default 1.5x)
"""

from dataclasses import dataclass


@dataclass
class BreakoutSignal:
    is_breakout: bool
    price: float
    resistance_level: float
    volume_ratio: float   # current volume / avg volume
    volume_confirmed: bool


def detect_breakout(
    close_prices: list[float],
    volumes: list[float],
    resistance_level: float,
    volume_avg_period: int = 20,
    volume_threshold: float = 1.5,
) -> BreakoutSignal:
    """Detect if a breakout occurred on the latest bar.

    Args:
        close_prices: Closing prices (oldest first).
        volumes: Volume data aligned with close_prices.
        resistance_level: Computed resistance level to break above.
        volume_avg_period: Period for average volume calculation.
        volume_threshold: Volume must exceed avg by this multiplier.

    Returns:
        BreakoutSignal with detection result.
    """
    if not close_prices or not volumes:
        return BreakoutSignal(False, 0, resistance_level, 0, False)

    current_price = close_prices[-1]
    current_volume = volumes[-1]

    # Volume ratio
    if len(volumes) >= volume_avg_period:
        avg_volume = sum(volumes[-volume_avg_period - 1:-1]) / volume_avg_period
    else:
        avg_volume = sum(volumes[:-1]) / max(len(volumes) - 1, 1) if len(volumes) > 1 else current_volume

    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    volume_confirmed = volume_ratio >= volume_threshold

    price_above_resistance = current_price > resistance_level
    is_breakout = price_above_resistance and volume_confirmed

    return BreakoutSignal(
        is_breakout=is_breakout,
        price=current_price,
        resistance_level=resistance_level,
        volume_ratio=volume_ratio,
        volume_confirmed=volume_confirmed,
    )
