"""Tests for Layer 3 entry/exit/addition rules."""

from app.services.technical.indicators.macd import MACDResult
from app.services.technical.indicators.breakout import BreakoutSignal
from app.services.technical.indicators.trendline import TrendlineResult
from app.services.technical.rules.entry import evaluate_entry
from app.services.technical.rules.exit import evaluate_exit
from app.services.technical.rules.addition import check_addition_cap


# --- Entry Rules ---

class TestEntryRules:
    def test_breakout_volume_macd_all_conditions_met(self):
        macd = MACDResult(macd_line=1, signal_line=0.5, histogram=0.5, bullish_crossover=True, bearish_crossover=False)
        breakout = BreakoutSignal(is_breakout=True, price=115, resistance_level=110, volume_ratio=2.0, volume_confirmed=True)
        signal = evaluate_entry("breakout_volume_macd", macd, breakout, volume_ratio=2.0)
        assert signal.triggered is True

    def test_breakout_volume_macd_no_breakout(self):
        macd = MACDResult(macd_line=1, signal_line=0.5, histogram=0.5, bullish_crossover=True, bearish_crossover=False)
        breakout = BreakoutSignal(is_breakout=False, price=105, resistance_level=110, volume_ratio=2.0, volume_confirmed=True)
        signal = evaluate_entry("breakout_volume_macd", macd, breakout, volume_ratio=2.0)
        assert signal.triggered is False

    def test_macd_consolidation_volume_all_met(self):
        macd = MACDResult(macd_line=1, signal_line=0.5, histogram=0.5, bullish_crossover=True, bearish_crossover=False)
        signal = evaluate_entry("macd_consolidation_volume", macd, None, volume_ratio=2.0, in_consolidation=True)
        assert signal.triggered is True

    def test_macd_consolidation_volume_not_consolidating(self):
        macd = MACDResult(macd_line=1, signal_line=0.5, histogram=0.5, bullish_crossover=True, bearish_crossover=False)
        signal = evaluate_entry("macd_consolidation_volume", macd, None, volume_ratio=2.0, in_consolidation=False)
        assert signal.triggered is False

    def test_breakout_volume_simple(self):
        breakout = BreakoutSignal(is_breakout=True, price=115, resistance_level=110, volume_ratio=2.0, volume_confirmed=True)
        signal = evaluate_entry("breakout_volume", None, breakout, volume_ratio=2.0)
        assert signal.triggered is True

    def test_unknown_rule(self):
        signal = evaluate_entry("invalid_rule", None, None, 1.0)
        assert signal.triggered is False


# --- Exit Rules ---

class TestExitRules:
    def test_eight_pct_drop_triggered(self):
        signal = evaluate_exit("eight_pct_drop", current_price=92, post_entry_high=110, macd=None, trendline=None)
        # Drop = (110-92)/110 = 16.4% — triggers 8% rule
        assert signal.triggered is True

    def test_eight_pct_drop_not_triggered(self):
        signal = evaluate_exit("eight_pct_drop", current_price=105, post_entry_high=110, macd=None, trendline=None)
        # Drop = (110-105)/110 = 4.5% — below 8%
        assert signal.triggered is False

    def test_macd_red_triggered(self):
        macd = MACDResult(macd_line=-0.5, signal_line=0, histogram=-0.5, bullish_crossover=False, bearish_crossover=True)
        signal = evaluate_exit("macd_red", current_price=100, post_entry_high=110, macd=macd, trendline=None)
        assert signal.triggered is True

    def test_macd_red_not_triggered(self):
        macd = MACDResult(macd_line=1, signal_line=0.5, histogram=0.5, bullish_crossover=False, bearish_crossover=False)
        signal = evaluate_exit("macd_red", current_price=100, post_entry_high=110, macd=macd, trendline=None)
        assert signal.triggered is False

    def test_trendline_breach_triggered(self):
        trendline = TrendlineResult(slope=0.5, intercept=90, current_trendline_value=105, price_above_trendline=False, breach_detected=True)
        signal = evaluate_exit("trendline_breach", current_price=100, post_entry_high=110, macd=None, trendline=trendline)
        assert signal.triggered is True

    def test_trendline_breach_not_triggered(self):
        trendline = TrendlineResult(slope=0.5, intercept=90, current_trendline_value=95, price_above_trendline=True, breach_detected=False)
        signal = evaluate_exit("trendline_breach", current_price=100, post_entry_high=110, macd=None, trendline=trendline)
        assert signal.triggered is False


# --- Addition Cap ---

class TestAdditionCap:
    def test_within_5pct_cap(self):
        result = check_addition_cap("max_5_pct", position_value=4000, portfolio_value=100000)
        assert result.allowed is True
        assert result.current_allocation_pct == 4.0

    def test_exceeds_5pct_cap(self):
        result = check_addition_cap("max_5_pct", position_value=4000, portfolio_value=100000, proposed_addition=2000)
        assert result.allowed is False  # 6% > 5%

    def test_10pct_cap_allows_more(self):
        result = check_addition_cap("max_10_pct", position_value=8000, portfolio_value=100000, proposed_addition=1000)
        assert result.allowed is True  # 9% < 10%

    def test_12pct_cap(self):
        result = check_addition_cap("max_12_pct", position_value=11000, portfolio_value=100000, proposed_addition=500)
        assert result.allowed is True  # 11.5% < 12%

    def test_remaining_calculation(self):
        result = check_addition_cap("max_10_pct", position_value=7000, portfolio_value=100000)
        assert result.remaining_pct == 3.0

    def test_unknown_rule(self):
        result = check_addition_cap("max_99_pct", position_value=1000, portfolio_value=100000)
        assert result.allowed is False
