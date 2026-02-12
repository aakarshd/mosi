"""Earnings transcript vendor adapter.

Vendor TBD (StockEdge / Tijori / Trendlyne). Built with adapter pattern
so vendor can be swapped without changing the rest of the pipeline.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TranscriptAdapter(ABC):
    """Abstract adapter for earnings transcript vendors."""

    @abstractmethod
    async def fetch_transcripts(self, symbol: str, last_n_quarters: int = 3) -> list[dict]:
        """Fetch earnings call transcripts for a stock.

        Returns list of dicts: {url, quarter_label, call_date, title}
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...


class StockEdgeAdapter(TranscriptAdapter):
    """StockEdge transcript adapter — placeholder."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def fetch_transcripts(self, symbol: str, last_n_quarters: int = 3) -> list[dict]:
        raise NotImplementedError("StockEdge adapter pending vendor selection and API contract")

    async def health_check(self) -> bool:
        return False


class TijoriAdapter(TranscriptAdapter):
    """Tijori Finance transcript adapter — placeholder."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def fetch_transcripts(self, symbol: str, last_n_quarters: int = 3) -> list[dict]:
        raise NotImplementedError("Tijori adapter pending vendor selection and API contract")

    async def health_check(self) -> bool:
        return False
