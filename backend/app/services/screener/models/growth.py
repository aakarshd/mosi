"""Growth Screener Model.

Criteria (exact from MOSI Algorithm):
  1. Market Cap > 1000 Cr
  2. Revenue Growth QoQ YoY > 25%
  3. OPM Growth > 30%
  4. ROCE >= 15%
  5. Institutional holding support: FII QoQ >= 0, Promoter QoQ >= 0, Institutional QoQ >= 0
  6. EPS Growth > 40% OR Net Profit Growth > 40%

Logic: High-growth companies with strong operational metrics and
institutional investor confidence.
"""

from dataclasses import dataclass

from app.services.screener.adapters.base import FinancialData


@dataclass
class CriterionResult:
    name: str
    passed: bool
    value: float | str | None
    threshold: float | str | None


class GrowthModel:
    MODEL_TYPE = "growth"

    MCAP_MIN_CR = 1000.0
    REVENUE_GROWTH_MIN = 25.0
    OPM_GROWTH_MIN = 30.0
    ROCE_MIN = 15.0
    EPS_GROWTH_MIN = 40.0
    NET_PROFIT_GROWTH_MIN = 40.0

    def evaluate(self, stock: FinancialData) -> tuple[bool, float, list[CriterionResult]]:
        """Evaluate a stock against Growth criteria.

        Returns: (qualified, score, criteria_results)
        """
        criteria = []

        # 1. Market Cap > 1000 Cr
        mcap_pass = stock.market_cap_cr > self.MCAP_MIN_CR
        criteria.append(CriterionResult("MCap > 1000 Cr", mcap_pass, stock.market_cap_cr, self.MCAP_MIN_CR))

        # 2. Revenue Growth QoQ YoY > 25%
        rev_growth = max(
            stock.revenue_growth_qoq_pct or 0,
            stock.revenue_growth_yoy_pct or 0,
        )
        rev_pass = rev_growth > self.REVENUE_GROWTH_MIN
        criteria.append(CriterionResult("Revenue Growth > 25%", rev_pass, rev_growth, self.REVENUE_GROWTH_MIN))

        # 3. OPM Growth > 30%
        opm_pass = stock.opm_growth_pct is not None and stock.opm_growth_pct > self.OPM_GROWTH_MIN
        criteria.append(CriterionResult("OPM Growth > 30%", opm_pass, stock.opm_growth_pct, self.OPM_GROWTH_MIN))

        # 4. ROCE >= 15%
        roce_pass = stock.roce_pct is not None and stock.roce_pct >= self.ROCE_MIN
        criteria.append(CriterionResult("ROCE >= 15%", roce_pass, stock.roce_pct, self.ROCE_MIN))

        # 5. Institutional holding support (all three QoQ >= 0)
        fii_ok = stock.fii_holding_change_qoq is not None and stock.fii_holding_change_qoq >= 0
        promoter_ok = stock.promoter_holding_change_qoq is not None and stock.promoter_holding_change_qoq >= 0
        institutional_ok = stock.institutional_holding_change_qoq is not None and stock.institutional_holding_change_qoq >= 0
        holdings_pass = fii_ok and promoter_ok and institutional_ok

        holdings_value = f"FII:{stock.fii_holding_change_qoq}, Promoter:{stock.promoter_holding_change_qoq}, Inst:{stock.institutional_holding_change_qoq}"
        criteria.append(CriterionResult("Holdings QoQ >= 0", holdings_pass, holdings_value, ">= 0 all three"))

        # 6. EPS Growth > 40% OR Net Profit Growth > 40%
        eps_ok = stock.eps_growth_pct is not None and stock.eps_growth_pct > self.EPS_GROWTH_MIN
        np_ok = stock.net_profit_growth_pct is not None and stock.net_profit_growth_pct > self.NET_PROFIT_GROWTH_MIN
        earnings_pass = eps_ok or np_ok

        earnings_value = f"EPS:{stock.eps_growth_pct}, NP:{stock.net_profit_growth_pct}"
        criteria.append(CriterionResult("EPS/NP Growth > 40%", earnings_pass, earnings_value, self.EPS_GROWTH_MIN))

        qualified = all(c.passed for c in criteria)
        passed_count = sum(1 for c in criteria if c.passed)
        score = (passed_count / len(criteria)) * 100

        return qualified, score, criteria
