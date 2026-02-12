"""RSI (Relative Strength Index) indicator.

Default: 14-period. For Layer 1 PE Expansion model, uses weekly RSI.
For Layer 3 rules, can use daily RSI.
"""


def compute_rsi(close_prices: list[float], period: int = 14) -> float | None:
    """Compute RSI from closing prices.

    Args:
        close_prices: List of closing prices (oldest first). Needs period+1 values minimum.
        period: RSI period (default 14).

    Returns:
        RSI value (0-100), or None if insufficient data.
    """
    if len(close_prices) < period + 1:
        return None

    # Calculate price changes
    changes = [close_prices[i] - close_prices[i - 1] for i in range(1, len(close_prices))]

    # Initial average gain/loss (SMA of first `period` changes)
    gains = [max(c, 0) for c in changes[:period]]
    losses = [abs(min(c, 0)) for c in changes[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Smooth with Wilder's method for remaining changes
    for change in changes[period:]:
        gain = max(change, 0)
        loss = abs(min(change, 0))
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
