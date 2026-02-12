"""MACD (Moving Average Convergence Divergence) indicator.

Default parameters: fast=12, slow=26, signal=9
"""

from dataclasses import dataclass


@dataclass
class MACDResult:
    macd_line: float      # MACD line = EMA(fast) - EMA(slow)
    signal_line: float    # Signal line = EMA(signal) of MACD line
    histogram: float      # Histogram = MACD line - Signal line
    bullish_crossover: bool   # MACD crossed above signal
    bearish_crossover: bool   # MACD crossed below signal (turning red)


def _ema(prices: list[float], period: int) -> list[float]:
    """Compute Exponential Moving Average."""
    if len(prices) < period:
        return []
    multiplier = 2 / (period + 1)
    ema_values = [sum(prices[:period]) / period]  # SMA for first value
    for price in prices[period:]:
        ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def compute_macd(
    close_prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> MACDResult | None:
    """Compute MACD from closing prices.

    Args:
        close_prices: List of closing prices (oldest first).
        fast_period: Fast EMA period (default 12).
        slow_period: Slow EMA period (default 26).
        signal_period: Signal line EMA period (default 9).

    Returns:
        MACDResult with current values and crossover detection, or None if insufficient data.
    """
    min_data = slow_period + signal_period
    if len(close_prices) < min_data:
        return None

    fast_ema = _ema(close_prices, fast_period)
    slow_ema = _ema(close_prices, slow_period)

    # Align EMAs — slow_ema starts later
    offset = slow_period - fast_period
    macd_line_values = [f - s for f, s in zip(fast_ema[offset:], slow_ema)]

    if len(macd_line_values) < signal_period:
        return None

    signal_values = _ema(macd_line_values, signal_period)

    if len(signal_values) < 2:
        return None

    # Current values
    macd_current = macd_line_values[-1]
    signal_current = signal_values[-1]
    histogram = macd_current - signal_current

    # Previous values for crossover detection
    macd_prev = macd_line_values[-2]
    signal_offset = signal_period - 1
    signal_prev = signal_values[-2]

    bullish = macd_prev <= signal_prev and macd_current > signal_current
    bearish = macd_prev >= signal_prev and macd_current < signal_current

    return MACDResult(
        macd_line=macd_current,
        signal_line=signal_current,
        histogram=histogram,
        bullish_crossover=bullish,
        bearish_crossover=bearish,
    )
