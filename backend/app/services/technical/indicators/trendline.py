"""Trendline computation using linear regression on price pivots.

Used for exit rule: "Support Trendline Breach" — price breaks below
the computed support trendline.
"""

from dataclasses import dataclass


@dataclass
class TrendlineResult:
    slope: float              # Trendline slope (positive = uptrend)
    intercept: float          # Y-intercept
    current_trendline_value: float  # Trendline value at latest bar
    price_above_trendline: bool
    breach_detected: bool     # Price just crossed below trendline


def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    """Simple linear regression returning (slope, intercept)."""
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)

    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0.0, sum_y / n if n > 0 else 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def compute_trendline(
    lows: list[float],
    window: int = 5,
    lookback: int = 50,
) -> TrendlineResult | None:
    """Compute support trendline from swing lows.

    Args:
        lows: Low prices (oldest first).
        window: Window for swing low detection.
        lookback: How many bars to look back for trendline.

    Returns:
        TrendlineResult or None if insufficient data.
    """
    if len(lows) < lookback:
        return None

    recent_lows = lows[-lookback:]

    # Find swing lows
    swing_low_indices = []
    swing_low_values = []
    for i in range(window, len(recent_lows) - window):
        if recent_lows[i] == min(recent_lows[i - window : i + window + 1]):
            swing_low_indices.append(float(i))
            swing_low_values.append(recent_lows[i])

    if len(swing_low_indices) < 2:
        return None

    # Fit trendline through swing lows
    slope, intercept = _linear_regression(swing_low_indices, swing_low_values)

    # Current trendline value (at the last bar position)
    current_position = float(len(recent_lows) - 1)
    trendline_value = slope * current_position + intercept

    current_price = recent_lows[-1]
    price_above = current_price > trendline_value

    # Breach: previous bar was above, current is below
    if len(recent_lows) >= 2:
        prev_position = float(len(recent_lows) - 2)
        prev_trendline = slope * prev_position + intercept
        prev_above = recent_lows[-2] > prev_trendline
        breach = prev_above and not price_above
    else:
        breach = False

    return TrendlineResult(
        slope=slope,
        intercept=intercept,
        current_trendline_value=trendline_value,
        price_above_trendline=price_above,
        breach_detected=breach,
    )
