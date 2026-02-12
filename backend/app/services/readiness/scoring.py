"""MOSI Score computation — weighted composite of all 3 layers.

Score range: 0-100
- Layer 1 (screener strength): 0-33.3
- Layer 2 (AI Multi-Bagger Score): 0-33.3
- Signal source (alignment): 0-33.3

Weights are configurable; starting with equal 33/33/33.
"""

from dataclasses import dataclass

from app.services.readiness.classification import LayerInputs

# Default weights — equal weighting, to be tuned via backtest
LAYER1_WEIGHT = 1 / 3
LAYER2_WEIGHT = 1 / 3
SIGNAL_WEIGHT = 1 / 3


@dataclass
class ScoreBreakdown:
    """Per-layer contribution to the composite MOSI Score."""
    layer1_contribution: float
    layer2_contribution: float
    signal_contribution: float
    total: float
    layer1_raw: float  # The raw input value
    layer2_raw: float
    signal_raw: float


def compute_mosi_score(inputs: LayerInputs) -> ScoreBreakdown:
    """Compute the MOSI Score (0-100) with per-layer breakdown.

    Layer 1 raw: 0-100 screener score
    Layer 2 raw: 0-10 Multi-Bagger Score → normalized to 0-100
    Signal raw: composite of entry/exit/confidence → 0-100
    """
    # Layer 1: already 0-100
    layer1_raw = inputs.layer1_score if inputs.layer1_qualified else 0.0

    # Layer 2: Multi-Bagger Score is 0-10 → scale to 0-100
    layer2_raw = inputs.layer2_multi_bagger_score * 10.0

    # Signal source: compute from SignalResult
    signal_raw = _compute_signal_score(inputs)

    # Weighted sum
    layer1_contribution = layer1_raw * LAYER1_WEIGHT
    layer2_contribution = layer2_raw * LAYER2_WEIGHT
    signal_contribution = signal_raw * SIGNAL_WEIGHT

    total = round(layer1_contribution + layer2_contribution + signal_contribution, 1)
    total = max(0.0, min(100.0, total))

    return ScoreBreakdown(
        layer1_contribution=round(layer1_contribution, 1),
        layer2_contribution=round(layer2_contribution, 1),
        signal_contribution=round(signal_contribution, 1),
        total=total,
        layer1_raw=round(layer1_raw, 1),
        layer2_raw=round(layer2_raw, 1),
        signal_raw=round(signal_raw, 1),
    )


def _compute_signal_score(inputs: LayerInputs) -> float:
    """Convert signal result to a 0-100 score.

    Scoring logic:
    - Entry signal present: +50
    - No exit signal: +30
    - Confidence bonus: up to +20 (confidence * 20)
    """
    score = 0.0

    if inputs.signal_result.has_entry_signal:
        score += 50.0

    if not inputs.signal_result.has_exit_signal:
        score += 30.0

    score += inputs.signal_result.confidence * 20.0

    return min(100.0, score)
