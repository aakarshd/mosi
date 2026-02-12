"""PE Expansion Screener Model.

Criteria (exact from MOSI Algorithm):
  1. PE TTM > PE 3yr average
  2. ROCE > 15%
  3. Market Cap > 1000 Cr
  4. EPS Growth > 40%
  5. OPM Growth > 30%
  6. Weekly RSI > 50
  7. Revenue Growth > 25%

Logic: Stocks undergoing PE re-rating with strong growth fundamentals
and positive technical momentum (RSI confirms uptrend).
"""

from dataclasses import dataclass

from app.services.screener.adapters.base import FinancialData


@dataclass
class CriterionResult:
    name: str
    passed: bool
    value: float | str | None
    threshold: float | str | None


class PeExpansionModel:
    MODEL_TYPE = "pe_expansion"

    ROCE_MIN = 15.0
    MCAP_MIN_CR = 1000.0
    EPS_GROWTH_MIN = 40.0
    OPM_GROWTH_MIN = 30.0
    RSI_MIN = 50.0
    REVENUE_GROWTH_MIN = 25.0

    def evaluate(self, stock: FinancialData) -> tuple[bool, float, list[CriterionResult]]:
        """Evaluate a stock against PE Expansion criteria.

        Returns: (qualified, score, criteria_results)
        """
        criteria = []

        # 1. PE TTM > PE 3yr avg
        pe_pass = (
            stock.pe_ttm is not None
            and stock.pe_3yr_avg is not None
            and stock.pe_ttm > stock.pe_3yr_avg
        )
        criteria.append(CriterionResult("PE TTM > PE 3yr avg", pe_pass, stock.pe_ttm, stock.pe_3yr_avg))

        # 2. ROCE > 15%
        roce_pass = stock.roce_pct is not None and stock.roce_pct > self.ROCE_MIN
        criteria.append(CriterionResult("ROCE > 15%", roce_pass, stock.roce_pct, self.ROCE_MIN))

        # 3. Market Cap > 1000 Cr
        mcap_pass = stock.market_cap_cr > self.MCAP_MIN_CR
        criteria.append(CriterionResult("MCap > 1000 Cr", mcap_pass, stock.market_cap_cr, self.MCAP_MIN_CR))

        # 4. EPS Growth > 40%
        eps_pass = stock.eps_growth_pct is not None and stock.eps_growth_pct > self.EPS_GROWTH_MIN
        criteria.append(CriterionResult("EPS Growth > 40%", eps_pass, stock.eps_growth_pct, self.EPS_GROWTH_MIN))

        # 5. OPM Growth > 30%
        opm_pass = stock.opm_growth_pct is not None and stock.opm_growth_pct > self.OPM_GROWTH_MIN
        criteria.append(CriterionResult("OPM Growth > 30%", opm_pass, stock.opm_growth_pct, self.OPM_GROWTH_MIN))

        # 6. Weekly RSI > 50
        rsi_pass = stock.weekly_rsi is not None and stock.weekly_rsi > self.RSI_MIN
        criteria.append(CriterionResult("Weekly RSI > 50", rsi_pass, stock.weekly_rsi, self.RSI_MIN))

        # 7. Revenue Growth > 25%
        rev_growth = max(
            stock.revenue_growth_qoq_pct or 0,
            stock.revenue_growth_yoy_pct or 0,
        )
        rev_pass = rev_growth > self.REVENUE_GROWTH_MIN
        criteria.append(CriterionResult("Revenue Growth > 25%", rev_pass, rev_growth, self.REVENUE_GROWTH_MIN))

        qualified = all(c.passed for c in criteria)
        passed_count = sum(1 for c in criteria if c.passed)
        score = (passed_count / len(criteria)) * 100

        return qualified, score, criteria
