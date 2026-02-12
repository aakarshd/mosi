"""BSE XBRL data source adapter.

Placeholder implementation — requires BSE XBRL API documentation and access.
The adapter pattern allows swapping this with a vendor API client once the
data source decision is finalized.
"""

from datetime import date

from app.services.screener.adapters.base import DataSourceAdapter, FinancialData


class BseXbrlAdapter(DataSourceAdapter):

    def __init__(self, base_url: str = "https://api.bseindia.com"):
        self.base_url = base_url

    async def fetch_all_stocks(self) -> list[FinancialData]:
        # TODO: Implement BSE XBRL parsing
        # 1. Fetch list of all listed companies from BSE
        # 2. For each company, fetch latest XBRL filing
        # 3. Parse XBRL to extract financial metrics
        # 4. Normalize into FinancialData objects
        raise NotImplementedError("BSE XBRL adapter pending data source finalization")

    async def fetch_stock(self, symbol: str) -> FinancialData | None:
        raise NotImplementedError("BSE XBRL adapter pending data source finalization")

    async def health_check(self) -> bool:
        # TODO: Ping BSE API
        return False
