"""Tests for Layer 1 screener models — exact criteria from MOSI Algorithm."""

from datetime import date

from app.services.screener.adapters.base import FinancialData
from app.services.screener.models import PassiveIncomeModel, GrowthModel, PeExpansionModel


def _make_stock(**overrides) -> FinancialData:
    """Helper to create a test stock with sensible defaults."""
    defaults = dict(
        symbol="TEST", isin="INE000000001", name="Test Stock", exchange="NSE",
        sector="IT", market_cap_cr=5000, roce_pct=20, opm_pct=25, opm_growth_pct=35,
        pe_ttm=30, pe_3yr_avg=22, pe_5yr_avg=20, pe_10yr_avg=18,
        revenue_growth_qoq_pct=30, revenue_growth_yoy_pct=30,
        eps_growth_pct=45, net_profit_growth_pct=45,
        fii_holding_change_qoq=0.5, promoter_holding_change_qoq=0.1,
        institutional_holding_change_qoq=0.3, weekly_rsi=60,
        data_date=date(2026, 1, 15), data_source="test",
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


# --- Passive Income Model ---

class TestPassiveIncomeModel:
    model = PassiveIncomeModel()

    def test_all_criteria_pass(self):
        stock = _make_stock(roce_pct=25, market_cap_cr=5000, pe_ttm=30, pe_3yr_avg=22, pe_5yr_avg=20, pe_10yr_avg=18)
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is True
        assert score == 100.0
        assert all(c.passed for c in criteria)

    def test_roce_below_threshold(self):
        stock = _make_stock(roce_pct=15)
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is False
        assert criteria[0].name == "ROCE > 18%"
        assert criteria[0].passed is False

    def test_mcap_below_threshold(self):
        stock = _make_stock(market_cap_cr=500)
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is False

    def test_pe_not_expanding_vs_3yr(self):
        stock = _make_stock(pe_ttm=20, pe_3yr_avg=25)
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is False
        assert criteria[2].passed is False  # PE TTM > PE 3yr avg

    def test_pe_not_expanding_vs_5yr(self):
        stock = _make_stock(pe_ttm=20, pe_5yr_avg=25)
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is False

    def test_pe_not_expanding_vs_10yr(self):
        stock = _make_stock(pe_ttm=15, pe_10yr_avg=20)
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is False

    def test_missing_roce_fails(self):
        stock = _make_stock(roce_pct=None)
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is False

    def test_score_reflects_partial_pass(self):
        stock = _make_stock(roce_pct=10, market_cap_cr=500)  # 2 failures
        _, score, criteria = self.model.evaluate(stock)
        passed = sum(1 for c in criteria if c.passed)
        assert score == (passed / len(criteria)) * 100


# --- Growth Model ---

class TestGrowthModel:
    model = GrowthModel()

    def test_all_criteria_pass(self):
        stock = _make_stock()
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is True
        assert score == 100.0

    def test_revenue_growth_below_threshold(self):
        stock = _make_stock(revenue_growth_qoq_pct=10, revenue_growth_yoy_pct=15)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_opm_growth_below_threshold(self):
        stock = _make_stock(opm_growth_pct=20)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_roce_below_threshold(self):
        stock = _make_stock(roce_pct=10)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_holdings_fii_declining(self):
        stock = _make_stock(fii_holding_change_qoq=-1.0)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_holdings_promoter_declining(self):
        stock = _make_stock(promoter_holding_change_qoq=-0.5)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_eps_or_np_growth_either_passes(self):
        # EPS below but NP above — should still pass earnings criterion
        stock = _make_stock(eps_growth_pct=20, net_profit_growth_pct=50)
        _, _, criteria = self.model.evaluate(stock)
        earnings_criterion = [c for c in criteria if "EPS" in c.name][0]
        assert earnings_criterion.passed is True

    def test_both_eps_np_below_fails(self):
        stock = _make_stock(eps_growth_pct=20, net_profit_growth_pct=20)
        qualified, _, criteria = self.model.evaluate(stock)
        assert qualified is False


# --- PE Expansion Model ---

class TestPeExpansionModel:
    model = PeExpansionModel()

    def test_all_criteria_pass(self):
        stock = _make_stock()
        qualified, score, criteria = self.model.evaluate(stock)
        assert qualified is True
        assert score == 100.0
        assert len(criteria) == 7

    def test_pe_not_expanding(self):
        stock = _make_stock(pe_ttm=18, pe_3yr_avg=25)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_rsi_below_50(self):
        stock = _make_stock(weekly_rsi=40)
        qualified, _, criteria = self.model.evaluate(stock)
        assert qualified is False
        rsi_criterion = [c for c in criteria if "RSI" in c.name][0]
        assert rsi_criterion.passed is False

    def test_eps_growth_below_threshold(self):
        stock = _make_stock(eps_growth_pct=20)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_revenue_growth_below_threshold(self):
        stock = _make_stock(revenue_growth_qoq_pct=10, revenue_growth_yoy_pct=15)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False

    def test_missing_rsi_fails(self):
        stock = _make_stock(weekly_rsi=None)
        qualified, _, _ = self.model.evaluate(stock)
        assert qualified is False
