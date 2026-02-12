"""Broker API price feed — subscribes to real-time tick stream.

Connects to existing broker integrations (Zerodha Kite/Dhan/Upstox).
This is an abstract interface — concrete implementations depend on
which broker's SDK is used.
"""

import logging
from abc import ABC, abstractmethod
from typing import Callable, Awaitable

from app.services.technical.state import OHLCV

logger = logging.getLogger(__name__)


class BrokerFeed(ABC):
    """Abstract broker price feed interface."""

    @abstractmethod
    async def subscribe(self, symbols: list[str], on_tick: Callable[[str, OHLCV], Awaitable[None]]) -> None:
        """Subscribe to real-time price ticks for given symbols.

        Args:
            symbols: List of stock symbols to subscribe to.
            on_tick: Async callback called with (symbol, ohlcv) on each tick.
        """
        ...

    @abstractmethod
    async def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from symbols."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from broker feed."""
        ...

    @abstractmethod
    async def get_historical_ohlcv(self, symbol: str, days: int = 200) -> list[OHLCV]:
        """Fetch historical OHLCV for initial state seeding."""
        ...


class ZerodhaKiteFeed(BrokerFeed):
    """Zerodha Kite Connect WebSocket feed — placeholder.

    Requires: kiteconnect SDK, API key, access token.
    Uses existing MOSI broker integration — not a new integration.
    """

    def __init__(self, api_key: str = "", access_token: str = ""):
        self.api_key = api_key
        self.access_token = access_token

    async def subscribe(self, symbols: list[str], on_tick: Callable[[str, OHLCV], Awaitable[None]]) -> None:
        # TODO: Connect to Kite WebSocket, subscribe to instrument tokens
        raise NotImplementedError("Zerodha Kite feed pending broker API provisioning")

    async def unsubscribe(self, symbols: list[str]) -> None:
        raise NotImplementedError

    async def disconnect(self) -> None:
        raise NotImplementedError

    async def get_historical_ohlcv(self, symbol: str, days: int = 200) -> list[OHLCV]:
        # TODO: Use Kite historical data API
        raise NotImplementedError


class DhanFeed(BrokerFeed):
    """Dhan API feed — placeholder."""

    async def subscribe(self, symbols, on_tick):
        raise NotImplementedError("Dhan feed pending broker API provisioning")

    async def unsubscribe(self, symbols):
        raise NotImplementedError

    async def disconnect(self):
        raise NotImplementedError

    async def get_historical_ohlcv(self, symbol, days=200):
        raise NotImplementedError
