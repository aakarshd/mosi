from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class FinancialData:
    """Normalized financial data for a single stock used by screener models."""
    symbol: str
    isin: str
    name: str
    exchange: str
    sector: str | None
    market_cap_cr: float  # Market cap in crores

    # Profitability
    roce_pct: float | None  # Return on Capital Employed %
    opm_pct: float | None   # Operating Profit Margin %
    opm_growth_pct: float | None  # OPM growth %

    # Valuation
    pe_ttm: float | None          # PE ratio (trailing twelve months)
    pe_3yr_avg: float | None      # PE average over 3 years
    pe_5yr_avg: float | None      # PE average over 5 years
    pe_10yr_avg: float | None     # PE average over 10 years

    # Growth
    revenue_growth_qoq_pct: float | None  # Revenue growth quarter over quarter %
    revenue_growth_yoy_pct: float | None  # Revenue growth year over year %
    eps_growth_pct: float | None          # EPS growth %
    net_profit_growth_pct: float | None   # Net profit growth %

    # Holdings
    fii_holding_change_qoq: float | None         # FII holding QoQ change (>=0 means stable/increasing)
    promoter_holding_change_qoq: float | None     # Promoter holding QoQ change
    institutional_holding_change_qoq: float | None  # DII holding QoQ change

    # Technical (needed for PE Expansion model)
    weekly_rsi: float | None  # 14-period weekly RSI

    # Metadata
    data_date: date
    data_source: str


class DataSourceAdapter(ABC):
    """Abstract adapter for financial data sources. Implement for BSE XBRL, vendor API, etc."""

    @abstractmethod
    async def fetch_all_stocks(self) -> list[FinancialData]:
        """Fetch financial data for the entire NSE/BSE universe."""
        ...

    @abstractmethod
    async def fetch_stock(self, symbol: str) -> FinancialData | None:
        """Fetch financial data for a single stock."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is available."""
        ...
