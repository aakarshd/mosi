"""Exit rule evaluation — 3 user-configurable options from MOSI Algorithm.

Option 1: 8% Drop from Top
  - Price drops 8% from the post-entry high (trailing stop)

Option 2: MACD Turning Red
  - MACD crosses below signal line (bearish crossover)

Option 3: Support Trendline Breach
  - Price breaks below computed support trendline
"""

from dataclasses import dataclass

from app.services.technical.indicators import MACDResult, TrendlineResult


@dataclass
class ExitSignal:
    triggered: bool
    rule_name: str
    reasons: list[str]


def evaluate_exit(
    rule: str,
    current_price: float,
    post_entry_high: float,
    macd: MACDResult | None,
    trendline: TrendlineResult | None,
) -> ExitSignal:
    """Evaluate exit rule for a held position.

    Args:
        rule: One of "eight_pct_drop", "macd_red", "trendline_breach"
        current_price: Current stock price.
        post_entry_high: Highest price since position entry.
        macd: Current MACD state.
        trendline: Current trendline state.

    Returns:
        ExitSignal with trigger status and reasons.
    """
    if rule == "eight_pct_drop":
        return _rule_eight_pct_drop(current_price, post_entry_high)
    elif rule == "macd_red":
        return _rule_macd_red(macd)
    elif rule == "trendline_breach":
        return _rule_trendline_breach(trendline, current_price)
    else:
        return ExitSignal(False, rule, [f"Unknown exit rule: {rule}"])


def _rule_eight_pct_drop(current_price: float, post_entry_high: float) -> ExitSignal:
    if post_entry_high <= 0:
        return ExitSignal(False, "eight_pct_drop", ["No valid post-entry high"])

    drop_pct = ((post_entry_high - current_price) / post_entry_high) * 100
    triggered = drop_pct >= 8.0

    if triggered:
        reason = f"Price dropped {drop_pct:.1f}% from high of {post_entry_high:.2f} (threshold: 8%)"
    else:
        reason = f"Price {drop_pct:.1f}% from high (threshold: 8%)"

    return ExitSignal(triggered, "eight_pct_drop", [reason])


def _rule_macd_red(macd: MACDResult | None) -> ExitSignal:
    if macd is None:
        return ExitSignal(False, "macd_red", ["Insufficient data for MACD"])

    if macd.bearish_crossover:
        return ExitSignal(True, "macd_red", ["MACD crossed below signal line (turning red)"])

    return ExitSignal(False, "macd_red", [f"MACD histogram: {macd.histogram:.4f} (no bearish crossover)"])


def _rule_trendline_breach(trendline: TrendlineResult | None, current_price: float) -> ExitSignal:
    if trendline is None:
        return ExitSignal(False, "trendline_breach", ["Insufficient data for trendline"])

    if trendline.breach_detected:
        return ExitSignal(
            True,
            "trendline_breach",
            [f"Price {current_price:.2f} broke below support trendline at {trendline.current_trendline_value:.2f}"],
        )

    return ExitSignal(
        False,
        "trendline_breach",
        [f"Price {current_price:.2f} above trendline {trendline.current_trendline_value:.2f}"],
    )
