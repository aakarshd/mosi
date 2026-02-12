"""Aarna API client — connects to Aarna signal endpoint.

Implements the ISignalSource interface so the readiness engine can
consume Aarna signals as an alternative to Layer 3 Technical Rules.

The Aarna API contract is TBD by the client. This implementation
provides a production-ready client structure with a stub fallback
for testing until the real API is available.
"""

import logging
from dataclasses import dataclass

import httpx

from app.services.readiness.signal_source import ISignalSource, SignalResult

logger = logging.getLogger(__name__)

# Default timeout for Aarna API calls
AARNA_TIMEOUT_SECONDS = 10


@dataclass
class AarnaConfig:
    base_url: str = ""
    api_key: str = ""
    timeout: int = AARNA_TIMEOUT_SECONDS
    enabled: bool = False


class AarnaClient(ISignalSource):
    """Production Aarna API client implementing ISignalSource."""

    def __init__(self, config: AarnaConfig):
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                headers={"Authorization": f"Bearer {self._config.api_key}"},
                timeout=self._config.timeout,
            )
        return self._client

    async def get_signal(self, symbol: str, user_id: str) -> SignalResult:
        if not self._config.enabled or not self._config.base_url:
            logger.debug(f"Aarna not configured, returning empty signal for {symbol}")
            return SignalResult()

        try:
            client = await self._get_client()
            response = await client.get(f"/signals/{symbol}", params={"user_id": user_id})
            response.raise_for_status()
            data = response.json()

            return SignalResult(
                has_entry_signal=data.get("entry_signal", False),
                has_exit_signal=data.get("exit_signal", False),
                entry_reasons=data.get("entry_reasons", []),
                exit_reasons=data.get("exit_reasons", []),
                confidence=data.get("confidence", 0.0),
                raw_data=data,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Aarna API error for {symbol}: {e.response.status_code}")
            return SignalResult()
        except httpx.RequestError as e:
            logger.error(f"Aarna API connection error for {symbol}: {e}")
            return SignalResult()

    def source_name(self) -> str:
        return "aarna"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def is_available(self) -> bool:
        return self._config.enabled and bool(self._config.base_url)


class AarnaStub(ISignalSource):
    """Stub Aarna for testing — returns configurable signals.

    Use set_signal() to configure what the stub returns per symbol.
    """

    def __init__(self):
        self._signals: dict[str, SignalResult] = {}

    def set_signal(self, symbol: str, signal: SignalResult) -> None:
        self._signals[symbol] = signal

    async def get_signal(self, symbol: str, user_id: str) -> SignalResult:
        return self._signals.get(symbol, SignalResult())

    def source_name(self) -> str:
        return "aarna"
