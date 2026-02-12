"""Tests for Task #11 — Aarna integration, signal source toggle, SEBI disclaimer."""

import pytest

from app.services.aarna.client import AarnaClient, AarnaStub, AarnaConfig
from app.services.readiness.signal_source import SignalResult
from app.middleware.sebi_disclaimer import (
    should_include_disclaimer,
    inject_disclaimer,
    SEBI_DISCLAIMER,
)


# --- Aarna Client Tests ---

class TestAarnaClient:
    def test_disabled_returns_empty_signal(self):
        config = AarnaConfig(enabled=False)
        client = AarnaClient(config)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            client.get_signal("RELIANCE", "user1")
        )
        assert result.has_entry_signal is False
        assert result.has_exit_signal is False

    def test_no_base_url_returns_empty(self):
        config = AarnaConfig(enabled=True, base_url="")
        client = AarnaClient(config)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            client.get_signal("RELIANCE", "user1")
        )
        assert result.has_entry_signal is False

    def test_source_name(self):
        config = AarnaConfig()
        client = AarnaClient(config)
        assert client.source_name() == "aarna"

    def test_is_available_disabled(self):
        config = AarnaConfig(enabled=False, base_url="https://api.aarna.io")
        client = AarnaClient(config)
        assert client.is_available() is False

    def test_is_available_no_url(self):
        config = AarnaConfig(enabled=True, base_url="")
        client = AarnaClient(config)
        assert client.is_available() is False

    def test_is_available_configured(self):
        config = AarnaConfig(enabled=True, base_url="https://api.aarna.io", api_key="test")
        client = AarnaClient(config)
        assert client.is_available() is True


# --- Aarna Stub Tests ---

class TestAarnaStub:
    @pytest.mark.asyncio
    async def test_default_empty_signal(self):
        stub = AarnaStub()
        result = await stub.get_signal("RELIANCE", "user1")
        assert result.has_entry_signal is False
        assert result.has_exit_signal is False

    @pytest.mark.asyncio
    async def test_set_entry_signal(self):
        stub = AarnaStub()
        stub.set_signal("RELIANCE", SignalResult(
            has_entry_signal=True,
            entry_reasons=["Aarna bullish signal"],
            confidence=0.9,
        ))
        result = await stub.get_signal("RELIANCE", "user1")
        assert result.has_entry_signal is True
        assert result.confidence == 0.9
        assert "Aarna" in result.entry_reasons[0]

    @pytest.mark.asyncio
    async def test_set_exit_signal(self):
        stub = AarnaStub()
        stub.set_signal("TCS", SignalResult(
            has_exit_signal=True,
            exit_reasons=["Aarna bearish reversal"],
        ))
        result = await stub.get_signal("TCS", "user1")
        assert result.has_exit_signal is True

    @pytest.mark.asyncio
    async def test_different_symbols(self):
        stub = AarnaStub()
        stub.set_signal("RELIANCE", SignalResult(has_entry_signal=True))
        stub.set_signal("TCS", SignalResult(has_exit_signal=True))

        r1 = await stub.get_signal("RELIANCE", "user1")
        r2 = await stub.get_signal("TCS", "user1")
        r3 = await stub.get_signal("INFY", "user1")

        assert r1.has_entry_signal is True
        assert r2.has_exit_signal is True
        assert r3.has_entry_signal is False

    def test_source_name(self):
        assert AarnaStub().source_name() == "aarna"

    @pytest.mark.asyncio
    async def test_stub_implements_interface(self):
        """Verify stub satisfies ISignalSource contract."""
        from app.services.readiness.signal_source import ISignalSource
        stub = AarnaStub()
        assert isinstance(stub, ISignalSource)
        result = await stub.get_signal("TEST", "user1")
        assert isinstance(result, SignalResult)
        assert isinstance(stub.source_name(), str)


# --- SEBI Disclaimer Tests ---

class TestSebiDisclaimer:
    def test_disclaimer_on_readiness_path(self):
        assert should_include_disclaimer("/api/v1/readiness/123") is True

    def test_disclaimer_on_analysis_path(self):
        assert should_include_disclaimer("/api/v1/analysis/456") is True

    def test_disclaimer_on_screener_path(self):
        assert should_include_disclaimer("/api/v1/screener/pe_expansion") is True

    def test_disclaimer_on_portfolio_path(self):
        assert should_include_disclaimer("/api/v1/portfolio/metrics") is True

    def test_no_disclaimer_on_health(self):
        assert should_include_disclaimer("/api/v1/health") is False

    def test_no_disclaimer_on_config(self):
        assert should_include_disclaimer("/api/v1/config/models") is False

    def test_no_disclaimer_on_journal(self):
        assert should_include_disclaimer("/api/v1/journal") is False

    def test_inject_disclaimer_adds_field(self):
        data = {"status": "ready_now", "mosi_score": 75.5}
        result = inject_disclaimer(data)
        assert "disclaimer" in result
        assert "SEBI" in result["disclaimer"]
        assert result["status"] == "ready_now"  # Original data preserved

    def test_disclaimer_text_contains_required_elements(self):
        assert "investment advice" in SEBI_DISCLAIMER.lower()
        assert "market risks" in SEBI_DISCLAIMER.lower()
        assert "financial advisor" in SEBI_DISCLAIMER.lower()
