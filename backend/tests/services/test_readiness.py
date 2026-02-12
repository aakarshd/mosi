"""Tests for Task #7 — Readiness Engine, classification, scoring, signal source."""

import pytest

from app.models.readiness import ReadinessLevel
from app.services.readiness.signal_source import SignalResult, Layer3SignalSource, AarnaSignalSource
from app.services.readiness.classification import classify_readiness, LayerInputs
from app.services.readiness.scoring import compute_mosi_score, ScoreBreakdown


def _inputs(**overrides) -> LayerInputs:
    """Helper to create LayerInputs with sensible defaults."""
    defaults = dict(
        layer1_qualified=True,
        layer1_model="pe_expansion",
        layer1_score=100.0,
        layer2_verdict="Buy",
        layer2_multi_bagger_score=7.5,
        signal_result=SignalResult(has_entry_signal=True, confidence=0.8),
        is_holding=False,
    )
    defaults.update(overrides)
    return LayerInputs(**defaults)


# --- Classification Tests ---

class TestClassification:
    def test_ready_now_all_layers_aligned(self):
        inputs = _inputs()
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.READY_NOW
        assert "All 3 layers aligned" in reason

    def test_getting_ready_buy_no_entry(self):
        inputs = _inputs(signal_result=SignalResult(has_entry_signal=False))
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.GETTING_READY
        assert "waiting for entry signal" in reason

    def test_getting_ready_hold_with_entry(self):
        inputs = _inputs(layer2_verdict="Hold", signal_result=SignalResult(has_entry_signal=True))
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.GETTING_READY
        assert "Hold" in reason

    def test_not_ready_hold_no_entry(self):
        inputs = _inputs(layer2_verdict="Hold", signal_result=SignalResult(has_entry_signal=False))
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.NOT_READY

    def test_not_ready_avoid_verdict(self):
        inputs = _inputs(layer2_verdict="Avoid")
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.NOT_READY
        assert "Avoid" in reason

    def test_not_ready_layer1_fail(self):
        inputs = _inputs(layer1_qualified=False)
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.NOT_READY
        assert "Layer 1" in reason

    def test_exit_alert_holding_exit_signal(self):
        inputs = _inputs(
            is_holding=True,
            signal_result=SignalResult(has_exit_signal=True, exit_reasons=["8% drop from high"]),
        )
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.EXIT_ALERT
        assert "8% drop" in reason

    def test_exit_alert_holding_avoid_verdict(self):
        inputs = _inputs(is_holding=True, layer2_verdict="Avoid")
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.EXIT_ALERT
        assert "Avoid" in reason

    def test_holding_without_exit_still_classifies_normally(self):
        inputs = _inputs(is_holding=True, signal_result=SignalResult(has_entry_signal=True))
        status, reason = classify_readiness(inputs)
        # Holding with buy + entry — still Ready Now (no exit signal)
        assert status == ReadinessLevel.READY_NOW

    def test_layer2_unavailable_with_entry(self):
        inputs = _inputs(layer2_verdict=None, signal_result=SignalResult(has_entry_signal=True))
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.GETTING_READY
        assert "reduced confidence" in reason

    def test_layer2_unavailable_no_entry(self):
        inputs = _inputs(layer2_verdict=None, signal_result=SignalResult(has_entry_signal=False))
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.NOT_READY
        assert "unavailable" in reason


# --- Scoring Tests ---

class TestMosiScore:
    def test_perfect_score(self):
        """All layers maxed out — score should be near 100."""
        inputs = _inputs(
            layer1_score=100.0,
            layer2_multi_bagger_score=10.0,
            signal_result=SignalResult(has_entry_signal=True, confidence=1.0),
        )
        breakdown = compute_mosi_score(inputs)
        assert breakdown.total == 100.0
        assert breakdown.layer1_contribution > 0
        assert breakdown.layer2_contribution > 0
        assert breakdown.signal_contribution > 0

    def test_zero_score(self):
        """All layers zeroed — score should be 0."""
        inputs = _inputs(
            layer1_qualified=False,
            layer1_score=0.0,
            layer2_multi_bagger_score=0.0,
            signal_result=SignalResult(has_exit_signal=True, confidence=0.0),
        )
        breakdown = compute_mosi_score(inputs)
        assert breakdown.total == 10.0  # Only the no-exit bonus is absent, but exit signal = no 30pts

    def test_equal_weighting(self):
        """Each layer contributes roughly 1/3."""
        inputs = _inputs(
            layer1_score=60.0,
            layer2_multi_bagger_score=6.0,
            signal_result=SignalResult(has_entry_signal=True, confidence=0.5),
        )
        breakdown = compute_mosi_score(inputs)
        assert 0 < breakdown.layer1_contribution < 100
        assert 0 < breakdown.layer2_contribution < 100
        assert 0 < breakdown.signal_contribution < 100
        # Total should be sum of contributions
        expected = breakdown.layer1_contribution + breakdown.layer2_contribution + breakdown.signal_contribution
        assert abs(breakdown.total - expected) < 0.2  # Rounding tolerance

    def test_signal_score_components(self):
        """Entry signal + no exit = high signal score."""
        inputs = _inputs(signal_result=SignalResult(has_entry_signal=True, confidence=0.8))
        breakdown = compute_mosi_score(inputs)
        # 50 (entry) + 30 (no exit) + 16 (0.8*20) = 96
        assert breakdown.signal_raw == 96.0

    def test_signal_score_exit_only(self):
        """Exit signal with no entry = lower signal score."""
        inputs = _inputs(signal_result=SignalResult(has_exit_signal=True, confidence=0.5))
        breakdown = compute_mosi_score(inputs)
        # 0 (no entry) + 0 (has exit) + 10 (0.5*20) = 10
        assert breakdown.signal_raw == 10.0

    def test_score_capped_at_100(self):
        inputs = _inputs(layer1_score=100.0, layer2_multi_bagger_score=10.0)
        breakdown = compute_mosi_score(inputs)
        assert breakdown.total <= 100.0

    def test_score_floor_at_0(self):
        inputs = _inputs(
            layer1_qualified=False,
            layer1_score=0.0,
            layer2_multi_bagger_score=0.0,
            signal_result=SignalResult(),
        )
        breakdown = compute_mosi_score(inputs)
        assert breakdown.total >= 0.0

    def test_layer2_raw_scaled_correctly(self):
        """Multi-bagger score (0-10) should be scaled to 0-100."""
        inputs = _inputs(layer2_multi_bagger_score=5.0)
        breakdown = compute_mosi_score(inputs)
        assert breakdown.layer2_raw == 50.0


# --- Signal Source Tests ---

class TestSignalSources:
    def test_layer3_source_name(self):
        source = Layer3SignalSource(technical_engine=None)
        assert source.source_name() == "layer3"

    def test_aarna_source_name(self):
        source = AarnaSignalSource()
        assert source.source_name() == "aarna"

    @pytest.mark.asyncio
    async def test_layer3_default_empty_signal(self):
        source = Layer3SignalSource(technical_engine=None)
        result = await source.get_signal("RELIANCE", "user1")
        assert result.has_entry_signal is False
        assert result.has_exit_signal is False

    @pytest.mark.asyncio
    async def test_aarna_stub_returns_empty(self):
        source = AarnaSignalSource()
        result = await source.get_signal("RELIANCE", "user1")
        assert result.has_entry_signal is False

    @pytest.mark.asyncio
    async def test_layer3_captures_entry_signal(self):
        source = Layer3SignalSource(technical_engine=None)

        # Simulate TechnicalEngine emitting an entry signal
        class FakeSignal:
            user_id = "user1"
            symbol = "RELIANCE"
            signal_type = "entry"
            triggered = True
            reasons = ["Breakout above resistance with volume confirmation"]
            indicator_snapshot = {"macd": {"line": 1.5}, "rsi": 68}

        await source.on_signal(FakeSignal())
        result = await source.get_signal("RELIANCE", "user1")
        assert result.has_entry_signal is True
        assert "Breakout" in result.entry_reasons[0]

    @pytest.mark.asyncio
    async def test_layer3_captures_exit_signal(self):
        source = Layer3SignalSource(technical_engine=None)

        class FakeSignal:
            user_id = "user1"
            symbol = "RELIANCE"
            signal_type = "exit"
            triggered = True
            reasons = ["8% drop from post-entry high"]
            indicator_snapshot = {}

        await source.on_signal(FakeSignal())
        result = await source.get_signal("RELIANCE", "user1")
        assert result.has_exit_signal is True


# --- Edge Cases ---

class TestEdgeCases:
    def test_unknown_verdict_returns_not_ready(self):
        inputs = _inputs(layer2_verdict="StrongBuy")
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.NOT_READY
        assert "Unrecognized" in reason

    def test_exit_alert_priority_over_ready(self):
        """Exit signal while holding overrides even if all layers say buy."""
        inputs = _inputs(
            is_holding=True,
            layer2_verdict="Buy",
            signal_result=SignalResult(has_entry_signal=True, has_exit_signal=True, exit_reasons=["MACD bearish crossover"]),
        )
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.EXIT_ALERT

    def test_layer1_fail_overrides_everything(self):
        """Layer 1 fail means Not Ready regardless of L2 and signal."""
        inputs = _inputs(
            layer1_qualified=False,
            layer2_verdict="Buy",
            signal_result=SignalResult(has_entry_signal=True),
        )
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.NOT_READY
