"""Passive Income Screener Model.

Criteria (exact from MOSI Algorithm):
  1. ROCE > 18%
  2. Market Cap > 1000 Cr
  3. PE TTM > PE 3yr average
  4. PE TTM > PE 5yr average
  5. PE TTM > PE 10yr average

Logic: Stocks with high capital efficiency (ROCE) trading at historically
elevated PE multiples — suggests market is re-rating the stock.
"""

from dataclasses import dataclass

from app.services.screener.adapters.base import FinancialData


@dataclass
class CriterionResult:
    name: str
    passed: bool
    value: float | str | None
    threshold: float | str | None


class PassiveIncomeModel:
    MODEL_TYPE = "passive_income"

    ROCE_MIN = 18.0
    MCAP_MIN_CR = 1000.0

    def evaluate(self, stock: FinancialData) -> tuple[bool, float, list[CriterionResult]]:
        """Evaluate a stock against Passive Income criteria.

        Returns: (qualified, score, criteria_results)
        """
        criteria = []

        # 1. ROCE > 18%
        roce_pass = stock.roce_pct is not None and stock.roce_pct > self.ROCE_MIN
        criteria.append(CriterionResult("ROCE > 18%", roce_pass, stock.roce_pct, self.ROCE_MIN))

        # 2. Market Cap > 1000 Cr
        mcap_pass = stock.market_cap_cr > self.MCAP_MIN_CR
        criteria.append(CriterionResult("MCap > 1000 Cr", mcap_pass, stock.market_cap_cr, self.MCAP_MIN_CR))

        # 3. PE TTM > PE 3yr avg
        pe_3yr_pass = (
            stock.pe_ttm is not None
            and stock.pe_3yr_avg is not None
            and stock.pe_ttm > stock.pe_3yr_avg
        )
        criteria.append(CriterionResult("PE TTM > PE 3yr avg", pe_3yr_pass, stock.pe_ttm, stock.pe_3yr_avg))

        # 4. PE TTM > PE 5yr avg
        pe_5yr_pass = (
            stock.pe_ttm is not None
            and stock.pe_5yr_avg is not None
            and stock.pe_ttm > stock.pe_5yr_avg
        )
        criteria.append(CriterionResult("PE TTM > PE 5yr avg", pe_5yr_pass, stock.pe_ttm, stock.pe_5yr_avg))

        # 5. PE TTM > PE 10yr avg
        pe_10yr_pass = (
            stock.pe_ttm is not None
            and stock.pe_10yr_avg is not None
            and stock.pe_ttm > stock.pe_10yr_avg
        )
        criteria.append(CriterionResult("PE TTM > PE 10yr avg", pe_10yr_pass, stock.pe_ttm, stock.pe_10yr_avg))

        qualified = all(c.passed for c in criteria)
        passed_count = sum(1 for c in criteria if c.passed)
        score = (passed_count / len(criteria)) * 100

        return qualified, score, criteria
