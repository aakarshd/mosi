"""Third-party vendor API adapter.

Placeholder implementation — vendor selection is pending (Screener.in / others).
Implements the same DataSourceAdapter interface so it can be swapped with BSE XBRL.
"""

from app.services.screener.adapters.base import DataSourceAdapter, FinancialData


class VendorApiAdapter(DataSourceAdapter):

    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url

    async def fetch_all_stocks(self) -> list[FinancialData]:
        raise NotImplementedError("Vendor API adapter pending vendor selection")

    async def fetch_stock(self, symbol: str) -> FinancialData | None:
        raise NotImplementedError("Vendor API adapter pending vendor selection")

    async def health_check(self) -> bool:
        return False
