"""Readiness classification logic.

Determines stock readiness status based on the 3-layer pipeline:
- Ready Now: Layer 1 pass + Layer 2 Buy + signal source entry triggered
- Getting Ready: Layer 1 pass + Layer 2 Buy/Hold + signal source entry not triggered
- Not Ready: Layer 1 pass + Layer 2 Hold/Avoid, OR signal source unfavorable
- Exit Alert: Holding + signal source exit triggered, OR Layer 2 changed to Avoid
"""

from dataclasses import dataclass

from app.models.readiness import ReadinessLevel
from app.services.readiness.signal_source import SignalResult


@dataclass
class LayerInputs:
    """All 3-layer data needed for readiness classification."""
    layer1_qualified: bool
    layer1_model: str  # Model type that qualified the stock
    layer1_score: float  # 0-100 screener score

    layer2_verdict: str | None  # Buy/Hold/Avoid or None if unavailable
    layer2_multi_bagger_score: float  # 0-10

    signal_result: SignalResult

    is_holding: bool = False  # Whether user currently holds this stock


def classify_readiness(inputs: LayerInputs) -> tuple[ReadinessLevel, str]:
    """Classify stock readiness from 3-layer inputs.

    Returns:
        (ReadinessLevel, reason_text) — status and explanation of why.
    """
    # Exit Alert takes priority — user holds and exit signal active
    if inputs.is_holding:
        if inputs.signal_result.has_exit_signal:
            reasons = ", ".join(inputs.signal_result.exit_reasons) if inputs.signal_result.exit_reasons else "Exit signal triggered"
            return ReadinessLevel.EXIT_ALERT, f"Exit signal: {reasons}"
        if inputs.layer2_verdict == "Avoid":
            return ReadinessLevel.EXIT_ALERT, "Layer 2 verdict changed to Avoid"

    # Layer 1 must pass for Ready Now or Getting Ready
    if not inputs.layer1_qualified:
        return ReadinessLevel.NOT_READY, "Layer 1 screener criteria not met"

    # Layer 2 verdict determines next classification
    verdict = inputs.layer2_verdict

    if verdict == "Buy":
        if inputs.signal_result.has_entry_signal:
            return ReadinessLevel.READY_NOW, "All 3 layers aligned: screener pass + AI Buy + entry signal"
        return ReadinessLevel.GETTING_READY, "Layer 1 pass + AI Buy, waiting for entry signal"

    if verdict == "Hold":
        if inputs.signal_result.has_entry_signal:
            return ReadinessLevel.GETTING_READY, "Layer 1 pass + entry signal, but AI verdict is Hold"
        return ReadinessLevel.NOT_READY, "Layer 1 pass but AI verdict is Hold and no entry signal"

    if verdict == "Avoid":
        return ReadinessLevel.NOT_READY, "AI verdict is Avoid"

    # Layer 2 unavailable — use Layer 1 + signal source only (reduced confidence)
    if verdict is None:
        if inputs.signal_result.has_entry_signal:
            return ReadinessLevel.GETTING_READY, "Layer 1 pass + entry signal (Layer 2 unavailable — reduced confidence)"
        return ReadinessLevel.NOT_READY, "Layer 1 pass only (Layer 2 unavailable)"

    return ReadinessLevel.NOT_READY, f"Unrecognized Layer 2 verdict: {verdict}"
