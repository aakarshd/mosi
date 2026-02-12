"""Tests for Layer 3 technical indicators."""

import pytest

from app.services.technical.indicators.macd import compute_macd
from app.services.technical.indicators.rsi import compute_rsi
from app.services.technical.indicators.breakout import detect_breakout
from app.services.technical.indicators.support_resistance import compute_levels
from app.services.technical.indicators.trendline import compute_trendline
from app.services.technical.indicators.volume import compute_volume_ratio


# --- MACD ---

class TestMACD:
    def test_insufficient_data_returns_none(self):
        assert compute_macd([1, 2, 3]) is None

    def test_computes_with_sufficient_data(self):
        # Generate 50 prices with an uptrend
        prices = [100 + i * 0.5 for i in range(50)]
        result = compute_macd(prices)
        assert result is not None
        assert isinstance(result.macd_line, float)
        assert isinstance(result.signal_line, float)
        assert isinstance(result.histogram, float)

    def test_uptrend_positive_macd(self):
        # Strong uptrend — MACD should be positive
        prices = [100 + i * 2 for i in range(50)]
        result = compute_macd(prices)
        assert result is not None
        assert result.macd_line > 0

    def test_bullish_crossover_detection(self):
        # Create data with a crossover: downtrend then sharp uptrend
        prices = [100 - i * 0.5 for i in range(40)]  # Downtrend
        prices += [prices[-1] + i * 3 for i in range(15)]  # Sharp up
        result = compute_macd(prices)
        assert result is not None
        # MACD should be improving (may or may not be exact crossover)
        assert result.histogram > 0 or result.macd_line > result.signal_line


# --- RSI ---

class TestRSI:
    def test_insufficient_data_returns_none(self):
        assert compute_rsi([1, 2, 3]) is None

    def test_strong_uptrend_high_rsi(self):
        prices = [100 + i for i in range(30)]
        rsi = compute_rsi(prices)
        assert rsi is not None
        assert rsi > 70  # Overbought

    def test_strong_downtrend_low_rsi(self):
        prices = [200 - i for i in range(30)]
        rsi = compute_rsi(prices)
        assert rsi is not None
        assert rsi < 30  # Oversold

    def test_rsi_range_0_to_100(self):
        import random
        random.seed(42)
        prices = [100 + random.uniform(-5, 5) for _ in range(30)]
        rsi = compute_rsi(prices)
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_flat_prices_rsi_near_50(self):
        # Alternating small gains/losses should give RSI near 50
        prices = [100 + (0.1 if i % 2 == 0 else -0.1) for i in range(30)]
        rsi = compute_rsi(prices)
        assert rsi is not None
        assert 40 < rsi < 60


# --- Breakout ---

class TestBreakout:
    def test_breakout_detected(self):
        closes = [100] * 20 + [115]  # Price jumps above resistance
        volumes = [1000] * 20 + [2000]  # Volume 2x average
        result = detect_breakout(closes, volumes, resistance_level=110)
        assert result.is_breakout is True
        assert result.volume_confirmed is True

    def test_no_breakout_below_resistance(self):
        closes = [100] * 20 + [105]
        volumes = [1000] * 20 + [2000]
        result = detect_breakout(closes, volumes, resistance_level=110)
        assert result.is_breakout is False

    def test_no_breakout_low_volume(self):
        closes = [100] * 20 + [115]
        volumes = [1000] * 20 + [500]  # Low volume
        result = detect_breakout(closes, volumes, resistance_level=110)
        assert result.is_breakout is False
        assert result.volume_confirmed is False

    def test_empty_data(self):
        result = detect_breakout([], [], resistance_level=100)
        assert result.is_breakout is False


# --- Support/Resistance ---

class TestSupportResistance:
    def test_insufficient_data_returns_none(self):
        assert compute_levels([1, 2], [1, 2], [1, 2]) is None

    def test_computes_levels(self):
        # Create data with clear swing highs and lows
        highs = [100 + (5 if i % 10 == 5 else 0) for i in range(30)]
        lows = [95 - (5 if i % 10 == 0 else 0) for i in range(30)]
        closes = [97 + (i % 3) for i in range(30)]
        result = compute_levels(highs, lows, closes)
        assert result is not None
        assert result.resistance >= result.support
        assert result.pivot > 0


# --- Trendline ---

class TestTrendline:
    def test_insufficient_data_returns_none(self):
        assert compute_trendline([1, 2, 3]) is None

    def test_uptrend_positive_slope(self):
        lows = [100 + i * 0.5 for i in range(60)]
        result = compute_trendline(lows)
        assert result is not None
        assert result.slope > 0

    def test_downtrend_negative_slope(self):
        lows = [200 - i * 0.5 for i in range(60)]
        result = compute_trendline(lows)
        assert result is not None
        assert result.slope < 0


# --- Volume ---

class TestVolume:
    def test_normal_volume(self):
        volumes = [1000] * 21
        ratio = compute_volume_ratio(volumes)
        assert abs(ratio - 1.0) < 0.01

    def test_high_volume(self):
        volumes = [1000] * 20 + [2000]
        ratio = compute_volume_ratio(volumes)
        assert abs(ratio - 2.0) < 0.01

    def test_insufficient_data(self):
        assert compute_volume_ratio([]) == 0.0
        assert compute_volume_ratio([100]) == 0.0
