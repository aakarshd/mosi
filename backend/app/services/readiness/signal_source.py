"""Signal source interface — abstract contract for Layer 3 and Aarna.

Both Layer 3 Technical Rules and Aarna implement this interface so the
readiness engine can consume entry/exit signals uniformly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SignalResult:
    """Normalized signal from any signal source."""
    has_entry_signal: bool = False
    has_exit_signal: bool = False
    entry_reasons: list[str] = field(default_factory=list)
    exit_reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1
    raw_data: dict = field(default_factory=dict)


class ISignalSource(ABC):
    """Abstract signal source — Layer 3 and Aarna both implement this."""

    @abstractmethod
    async def get_signal(self, symbol: str, user_id: str) -> SignalResult:
        """Get the current entry/exit signal for a stock+user pair."""

    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this signal source."""


class Layer3SignalSource(ISignalSource):
    """Wraps the Layer 3 TechnicalEngine to produce signals."""

    def __init__(self, technical_engine):
        self._engine = technical_engine
        self._latest_signals: dict[tuple[str, str], SignalResult] = {}

    async def on_signal(self, signal) -> None:
        """Callback registered with TechnicalEngine to capture latest signals."""
        key = (signal.user_id, signal.symbol)
        existing = self._latest_signals.get(key, SignalResult())

        if signal.signal_type == "entry" and signal.triggered:
            existing.has_entry_signal = True
            existing.entry_reasons = signal.reasons
        elif signal.signal_type == "exit" and signal.triggered:
            existing.has_exit_signal = True
            existing.exit_reasons = signal.reasons

        existing.raw_data = signal.indicator_snapshot
        existing.confidence = 0.8 if signal.triggered else 0.5
        self._latest_signals[key] = existing

    async def get_signal(self, symbol: str, user_id: str) -> SignalResult:
        key = (user_id, symbol)
        return self._latest_signals.get(key, SignalResult())

    def source_name(self) -> str:
        return "layer3"


class AarnaSignalSource(ISignalSource):
    """Aarna signal adapter — calls Aarna API and normalizes to SignalResult.

    Stub implementation until Aarna API contract is finalized.
    """

    def __init__(self, api_base_url: str = "", api_key: str = ""):
        self._api_base_url = api_base_url
        self._api_key = api_key

    async def get_signal(self, symbol: str, user_id: str) -> SignalResult:
        if not self._api_base_url:
            return SignalResult()

        # Production implementation will call Aarna API:
        # response = await httpx.AsyncClient().get(
        #     f"{self._api_base_url}/signals/{symbol}",
        #     headers={"Authorization": f"Bearer {self._api_key}"}
        # )
        # data = response.json()
        # return SignalResult(
        #     has_entry_signal=data.get("entry", False),
        #     has_exit_signal=data.get("exit", False),
        #     entry_reasons=data.get("entry_reasons", []),
        #     exit_reasons=data.get("exit_reasons", []),
        #     confidence=data.get("confidence", 0.0),
        #     raw_data=data,
        # )
        return SignalResult()

    def source_name(self) -> str:
        return "aarna"
