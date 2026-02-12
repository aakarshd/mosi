"""Addition cap rule — tracks cumulative position additions against user's cap.

Options from MOSI Algorithm:
  - Max 5% of portfolio per position
  - Max 10% of portfolio per position
  - Max 12% of portfolio per position
"""

from dataclasses import dataclass


CAP_MAP = {
    "max_5_pct": 5.0,
    "max_10_pct": 10.0,
    "max_12_pct": 12.0,
}


@dataclass
class AdditionCheck:
    allowed: bool
    current_allocation_pct: float
    cap_pct: float
    remaining_pct: float
    message: str


def check_addition_cap(
    cap_rule: str,
    position_value: float,
    portfolio_value: float,
    proposed_addition: float = 0,
) -> AdditionCheck:
    """Check if an addition to a position is within the user's cap.

    Args:
        cap_rule: One of "max_5_pct", "max_10_pct", "max_12_pct"
        position_value: Current position value (quantity * current price).
        portfolio_value: Total portfolio value.
        proposed_addition: Value of proposed addition (0 = just check status).

    Returns:
        AdditionCheck with status and details.
    """
    cap = CAP_MAP.get(cap_rule)
    if cap is None:
        return AdditionCheck(False, 0, 0, 0, f"Unknown addition cap rule: {cap_rule}")

    if portfolio_value <= 0:
        return AdditionCheck(False, 0, cap, 0, "Portfolio value is zero or negative")

    current_pct = (position_value / portfolio_value) * 100
    new_pct = ((position_value + proposed_addition) / portfolio_value) * 100 if proposed_addition > 0 else current_pct
    remaining = max(0, cap - current_pct)

    if new_pct > cap:
        return AdditionCheck(
            allowed=False,
            current_allocation_pct=current_pct,
            cap_pct=cap,
            remaining_pct=remaining,
            message=f"Addition would bring allocation to {new_pct:.1f}% (cap: {cap}%)",
        )

    return AdditionCheck(
        allowed=True,
        current_allocation_pct=current_pct,
        cap_pct=cap,
        remaining_pct=remaining,
        message=f"Within cap: {current_pct:.1f}% / {cap}% ({remaining:.1f}% remaining)",
    )
