"""End-to-end pipeline tests — full MOSI pipeline validation.

Tests the complete flow: Layer 1 screening → Layer 2 AI analysis →
Layer 3/Aarna signals → Readiness classification → MOSI Score.

These tests use synthetic data and stubs (no real DB or LLM) to validate
the pipeline logic end-to-end.
"""

import pytest
from datetime import date

from app.services.screener.adapters.base import FinancialData
from app.services.screener.models import PassiveIncomeModel, GrowthModel, PeExpansionModel
from app.services.analysis.parser import parse_llm_output, ParsedAnalysis
from app.services.analysis.scoring import compute_multi_bagger_score, compute_verdict
from app.services.technical.indicators.macd import compute_macd, MACDResult
from app.services.technical.indicators.breakout import detect_breakout, BreakoutSignal
from app.services.technical.rules.entry import evaluate_entry
from app.services.technical.rules.exit import evaluate_exit
from app.services.readiness.signal_source import SignalResult
from app.services.readiness.classification import classify_readiness, LayerInputs
from app.services.readiness.scoring import compute_mosi_score
from app.services.aarna.client import AarnaStub
from app.services.journal.behavioral import (
    detect_early_exit, detect_fomo_buying, compute_discipline_score,
)
from app.services.journal.learning import get_all_courses, get_courses_for_screen
from app.middleware.sebi_disclaimer import should_include_disclaimer, inject_disclaimer
from app.models.readiness import ReadinessLevel


def _make_stock(**overrides) -> FinancialData:
    defaults = dict(
        symbol="RELIANCE", isin="INE002A01018", name="Reliance Industries Ltd",
        exchange="NSE", sector="Energy", market_cap_cr=1500000,
        roce_pct=22, opm_pct=28, opm_growth_pct=35,
        pe_ttm=28, pe_3yr_avg=22, pe_5yr_avg=20, pe_10yr_avg=18,
        revenue_growth_qoq_pct=30, revenue_growth_yoy_pct=32,
        eps_growth_pct=45, net_profit_growth_pct=48,
        fii_holding_change_qoq=0.5, promoter_holding_change_qoq=0.1,
        institutional_holding_change_qoq=0.3, weekly_rsi=65,
        data_date=date(2026, 1, 15), data_source="test",
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


import json

SAMPLE_LLM_OUTPUT = json.dumps({
    "stock_symbol": "RELIANCE",
    "stock_name": "Reliance Industries Ltd",
    "analysis_points": [
        {
            "point_number": i,
            "title": f"Point {i}",
            "finding": f"Finding for point {i}",
            "classification": "Expansion" if i <= 3 else None,
            "score": 7.5 if i <= 8 else 5.0,
            "confidence": "High",
            "evidence": [f"AR page {i * 10}"],
            "red_flags": [],
        }
        for i in range(1, 12)
    ],
    "multi_bagger_score": 7.0,
    "verdict": "Buy",
    "verdict_reasoning": "Strong growth with PE expansion",
    "key_strengths": ["Revenue acceleration", "Margin expansion"],
    "key_risks": ["High valuation"],
    "confidence_level": "High",
    "documents_analyzed": ["annual_report_2025.pdf", "quarterly_results_q3.pdf"],
})


# --- Full Pipeline: Ready Now Scenario ---

class TestFullPipelineReadyNow:
    """Test a stock that qualifies across all 3 layers → Ready Now."""

    def test_layer1_all_models_qualify(self):
        stock = _make_stock()
        for Model in [PassiveIncomeModel, GrowthModel, PeExpansionModel]:
            model = Model()
            qualified, score, criteria = model.evaluate(stock)
            assert qualified is True, f"{Model.__name__} should qualify"
            assert score == 100.0

    def test_layer2_buy_verdict(self):
        analysis = parse_llm_output(SAMPLE_LLM_OUTPUT)
        assert analysis.stock_symbol == "RELIANCE"
        assert analysis.verdict == "Buy"
        mbs = compute_multi_bagger_score(analysis)
        assert mbs >= 6.0
        verdict = compute_verdict(mbs)
        assert verdict == "Buy"

    def test_layer3_entry_signal(self):
        macd = MACDResult(macd_line=1, signal_line=0.5, histogram=0.5,
                          bullish_crossover=True, bearish_crossover=False)
        breakout = BreakoutSignal(is_breakout=True, price=115,
                                   resistance_level=110, volume_ratio=2.0,
                                   volume_confirmed=True)
        signal = evaluate_entry("breakout_volume_macd", macd, breakout, volume_ratio=2.0)
        assert signal.triggered is True

    def test_readiness_ready_now(self):
        inputs = LayerInputs(
            layer1_qualified=True,
            layer1_model="pe_expansion",
            layer1_score=100.0,
            layer2_verdict="Buy",
            layer2_multi_bagger_score=7.0,
            signal_result=SignalResult(has_entry_signal=True, confidence=0.85),
        )
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.READY_NOW

    def test_mosi_score_high(self):
        inputs = LayerInputs(
            layer1_qualified=True,
            layer1_model="pe_expansion",
            layer1_score=100.0,
            layer2_verdict="Buy",
            layer2_multi_bagger_score=7.0,
            signal_result=SignalResult(has_entry_signal=True, confidence=0.85),
        )
        score = compute_mosi_score(inputs)
        assert score.total >= 70  # High MOSI Score expected

    def test_sebi_disclaimer_injected(self):
        data = {"status": "ready_now", "mosi_score": 85.0}
        result = inject_disclaimer(data)
        assert "disclaimer" in result


# --- Full Pipeline: Exit Alert Scenario ---

class TestFullPipelineExitAlert:
    """Test a held stock with exit signal → Exit Alert."""

    def test_layer3_exit_signal(self):
        macd = MACDResult(macd_line=-0.5, signal_line=0, histogram=-0.5,
                          bullish_crossover=False, bearish_crossover=True)
        signal = evaluate_exit("macd_red", current_price=100, post_entry_high=120,
                               macd=macd, trendline=None)
        assert signal.triggered is True

    def test_readiness_exit_alert_on_exit_signal(self):
        inputs = LayerInputs(
            layer1_qualified=True,
            layer1_model="growth",
            layer1_score=100.0,
            layer2_verdict="Buy",
            layer2_multi_bagger_score=7.0,
            signal_result=SignalResult(has_exit_signal=True, exit_reasons=["MACD bearish crossover"]),
            is_holding=True,
        )
        status, reason = classify_readiness(inputs)
        assert status == ReadinessLevel.EXIT_ALERT

    def test_readiness_exit_alert_on_avoid_verdict(self):
        inputs = LayerInputs(
            layer1_qualified=True,
            layer1_model="growth",
            layer1_score=80.0,
            layer2_verdict="Avoid",
            layer2_multi_bagger_score=2.0,
            signal_result=SignalResult(),
            is_holding=True,
        )
        status, _ = classify_readiness(inputs)
        assert status == ReadinessLevel.EXIT_ALERT


# --- Full Pipeline: Not Ready Scenario ---

class TestFullPipelineNotReady:
    """Test a stock that fails Layer 1 → Not Ready regardless of other layers."""

    def test_layer1_fail_forces_not_ready(self):
        stock = _make_stock(roce_pct=5, market_cap_cr=200)  # Fails all models
        for Model in [PassiveIncomeModel, GrowthModel, PeExpansionModel]:
            qualified, _, _ = Model().evaluate(stock)
            assert qualified is False

    def test_readiness_not_ready_despite_buy_and_entry(self):
        inputs = LayerInputs(
            layer1_qualified=False,
            layer1_model="none",
            layer1_score=0.0,
            layer2_verdict="Buy",
            layer2_multi_bagger_score=8.0,
            signal_result=SignalResult(has_entry_signal=True, confidence=0.9),
        )
        status, _ = classify_readiness(inputs)
        assert status == ReadinessLevel.NOT_READY


# --- Full Pipeline: Aarna Path ---

class TestFullPipelineAarna:
    """Test readiness using Aarna as signal source instead of Layer 3."""

    @pytest.mark.asyncio
    async def test_aarna_entry_produces_ready_now(self):
        stub = AarnaStub()
        stub.set_signal("RELIANCE", SignalResult(
            has_entry_signal=True,
            entry_reasons=["Aarna bullish momentum"],
            confidence=0.9,
        ))

        signal = await stub.get_signal("RELIANCE", "user1")

        inputs = LayerInputs(
            layer1_qualified=True,
            layer1_model="pe_expansion",
            layer1_score=100.0,
            layer2_verdict="Buy",
            layer2_multi_bagger_score=7.0,
            signal_result=signal,
        )
        status, _ = classify_readiness(inputs)
        assert status == ReadinessLevel.READY_NOW

    @pytest.mark.asyncio
    async def test_aarna_exit_produces_exit_alert(self):
        stub = AarnaStub()
        stub.set_signal("TCS", SignalResult(
            has_exit_signal=True,
            exit_reasons=["Aarna trend reversal"],
        ))

        signal = await stub.get_signal("TCS", "user1")

        inputs = LayerInputs(
            layer1_qualified=True,
            layer1_model="growth",
            layer1_score=85.0,
            layer2_verdict="Buy",
            layer2_multi_bagger_score=6.5,
            signal_result=signal,
            is_holding=True,
        )
        status, _ = classify_readiness(inputs)
        assert status == ReadinessLevel.EXIT_ALERT

    @pytest.mark.asyncio
    async def test_aarna_no_signal_getting_ready(self):
        stub = AarnaStub()
        signal = await stub.get_signal("INFY", "user1")

        inputs = LayerInputs(
            layer1_qualified=True,
            layer1_model="pe_expansion",
            layer1_score=100.0,
            layer2_verdict="Buy",
            layer2_multi_bagger_score=7.0,
            signal_result=signal,
        )
        status, _ = classify_readiness(inputs)
        assert status == ReadinessLevel.GETTING_READY


# --- Cross-Layer Score Validation ---

class TestCrossLayerScoring:
    """Validate MOSI Score accurately reflects all layer contributions."""

    def test_all_layers_maxed(self):
        inputs = LayerInputs(
            layer1_qualified=True, layer1_model="pe_expansion", layer1_score=100.0,
            layer2_verdict="Buy", layer2_multi_bagger_score=10.0,
            signal_result=SignalResult(has_entry_signal=True, confidence=1.0),
        )
        score = compute_mosi_score(inputs)
        assert score.total == 100.0
        assert score.layer1_contribution > 30
        assert score.layer2_contribution > 30
        assert score.signal_contribution > 30

    def test_layer1_only(self):
        inputs = LayerInputs(
            layer1_qualified=True, layer1_model="growth", layer1_score=100.0,
            layer2_verdict=None, layer2_multi_bagger_score=0.0,
            signal_result=SignalResult(),
        )
        score = compute_mosi_score(inputs)
        assert score.layer1_contribution > 0
        assert score.layer2_contribution == 0
        assert score.total > 0 and score.total < 100

    def test_score_breakdown_adds_up(self):
        inputs = LayerInputs(
            layer1_qualified=True, layer1_model="growth", layer1_score=75.0,
            layer2_verdict="Hold", layer2_multi_bagger_score=5.0,
            signal_result=SignalResult(has_entry_signal=False, confidence=0.5),
        )
        score = compute_mosi_score(inputs)
        expected = score.layer1_contribution + score.layer2_contribution + score.signal_contribution
        assert abs(score.total - expected) < 0.2


# --- Behavioral Analysis Integration ---

class TestBehavioralIntegration:
    def test_discipline_score_in_ready_now_trades(self):
        trades = [
            {"stock_id": 1, "symbol": "RELIANCE", "trade_type": "buy", "quantity": 10,
             "price": 2500, "trade_date": date(2026, 1, 15),
             "mosi_context": {"readiness": {"status": "ready_now", "mosi_score": 85}}},
            {"stock_id": 2, "symbol": "TCS", "trade_type": "buy", "quantity": 5,
             "price": 3800, "trade_date": date(2026, 1, 20),
             "mosi_context": {"readiness": {"status": "ready_now", "mosi_score": 78}}},
        ]
        assert compute_discipline_score(trades) == 100.0

    def test_fomo_detected_when_not_ready(self):
        trades = [
            {"stock_id": 1, "symbol": "RELIANCE", "trade_type": "buy", "quantity": 10,
             "price": 2500, "trade_date": date(2026, 1, 15),
             "mosi_context": {"readiness": {"status": "not_ready"}}},
        ]
        patterns = detect_fomo_buying(trades)
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == "fomo_buy"


# --- Learning Center Integration ---

class TestLearningIntegration:
    def test_all_5_courses_available(self):
        assert len(get_all_courses()) == 5

    def test_screener_screen_has_courses(self):
        courses = get_courses_for_screen("screener_dashboard")
        assert len(courses) >= 1

    def test_layer2_screen_has_courses(self):
        courses = get_courses_for_screen("stock_detail_layer2")
        assert any(c.id == "reading-ai-analysis" for c in courses)


# --- SEBI Disclaimer Coverage ---

class TestSebiDisclaimerCoverage:
    def test_all_signal_paths_covered(self):
        """All paths that show signals/verdicts must include disclaimer."""
        signal_paths = [
            "/api/v1/readiness/123",
            "/api/v1/readiness",
            "/api/v1/analysis/456",
            "/api/v1/analysis/456/summary",
            "/api/v1/screener/pe_expansion",
            "/api/v1/portfolio/metrics",
        ]
        for path in signal_paths:
            assert should_include_disclaimer(path) is True, f"Missing disclaimer for {path}"

    def test_non_signal_paths_excluded(self):
        non_signal_paths = [
            "/api/v1/health",
            "/api/v1/config/models",
            "/api/v1/journal",
        ]
        for path in non_signal_paths:
            assert should_include_disclaimer(path) is False, f"Unexpected disclaimer for {path}"
