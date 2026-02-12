"""Tests for Task #10 — Journal auto-logging, behavioral pattern detection, learning center."""

from datetime import date, timedelta

from app.models.readiness import ReadinessLevel
from app.services.journal.behavioral import (
    detect_early_exit,
    detect_averaging_down,
    detect_ignored_exit_rules,
    detect_fomo_buying,
    detect_overtrading,
    compute_discipline_score,
)
from app.services.journal.learning import (
    get_all_courses,
    get_courses_for_screen,
    get_course_by_id,
)


def _trade(stock_id=1, symbol="TEST", trade_type="buy", price=100.0,
           trade_date=None, mosi_context=None):
    """Helper to build a trade dict."""
    return {
        "stock_id": stock_id,
        "symbol": symbol,
        "trade_type": trade_type,
        "quantity": 10,
        "price": price,
        "trade_date": trade_date or date(2026, 1, 15),
        "mosi_context": mosi_context or {},
    }


# --- Early Exit Detection ---

class TestEarlyExit:
    def test_detects_winner_sold_early(self):
        trades = [
            _trade(trade_type="buy", price=100.0, trade_date=date(2026, 1, 10)),
            _trade(trade_type="sell", price=110.0, trade_date=date(2026, 1, 13)),  # 3 days, 10% gain
        ]
        patterns = detect_early_exit(trades)
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == "early_exit"
        assert patterns[0]["days_held"] == 3
        assert patterns[0]["profit_pct"] == 10.0

    def test_no_pattern_if_held_long(self):
        trades = [
            _trade(trade_type="buy", price=100.0, trade_date=date(2026, 1, 1)),
            _trade(trade_type="sell", price=120.0, trade_date=date(2026, 2, 15)),  # 45 days
        ]
        patterns = detect_early_exit(trades)
        assert len(patterns) == 0

    def test_no_pattern_if_loss(self):
        trades = [
            _trade(trade_type="buy", price=100.0, trade_date=date(2026, 1, 10)),
            _trade(trade_type="sell", price=95.0, trade_date=date(2026, 1, 12)),  # Loss
        ]
        patterns = detect_early_exit(trades)
        assert len(patterns) == 0

    def test_small_gain_below_threshold_ignored(self):
        trades = [
            _trade(trade_type="buy", price=100.0, trade_date=date(2026, 1, 10)),
            _trade(trade_type="sell", price=103.0, trade_date=date(2026, 1, 13)),  # 3% < 5% threshold
        ]
        patterns = detect_early_exit(trades)
        assert len(patterns) == 0


# --- Averaging Down Detection ---

class TestAveragingDown:
    def test_detects_averaging_down(self):
        trades = [
            _trade(trade_type="buy", price=100.0),
            _trade(trade_type="add", price=90.0),  # Adding below entry
        ]
        patterns = detect_averaging_down(trades)
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == "averaging_down"
        assert patterns[0]["loss_pct"] == 10.0

    def test_adding_above_entry_is_ok(self):
        trades = [
            _trade(trade_type="buy", price=100.0),
            _trade(trade_type="add", price=110.0),  # Adding above entry
        ]
        patterns = detect_averaging_down(trades)
        assert len(patterns) == 0


# --- Ignored Exit Rules ---

class TestIgnoredExitRules:
    def test_detects_ignored_exit(self):
        trades = [
            _trade(
                trade_type="buy", stock_id=1,
                mosi_context={"readiness": {"status": "exit_alert"}},
            ),
        ]
        patterns = detect_ignored_exit_rules(trades)
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == "ignored_exit"

    def test_no_pattern_if_sold(self):
        trades = [
            _trade(
                trade_type="buy", stock_id=1,
                mosi_context={"readiness": {"status": "exit_alert"}},
            ),
            _trade(trade_type="sell", stock_id=1),
        ]
        patterns = detect_ignored_exit_rules(trades)
        assert len(patterns) == 0


# --- FOMO Buying ---

class TestFomoBuying:
    def test_detects_fomo(self):
        trades = [
            _trade(
                trade_type="buy",
                mosi_context={"readiness": {"status": "getting_ready"}},
            ),
        ]
        patterns = detect_fomo_buying(trades)
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == "fomo_buy"

    def test_no_fomo_when_ready_now(self):
        trades = [
            _trade(
                trade_type="buy",
                mosi_context={"readiness": {"status": "ready_now"}},
            ),
        ]
        patterns = detect_fomo_buying(trades)
        assert len(patterns) == 0

    def test_sell_trades_ignored(self):
        trades = [
            _trade(
                trade_type="sell",
                mosi_context={"readiness": {"status": "not_ready"}},
            ),
        ]
        patterns = detect_fomo_buying(trades)
        assert len(patterns) == 0


# --- Overtrading ---

class TestOvertrading:
    def test_detects_spike(self):
        trades = [_trade() for _ in range(10)]
        patterns = detect_overtrading(trades, baseline_monthly_count=3)
        assert len(patterns) == 1
        assert patterns[0]["pattern"] == "overtrading"
        assert patterns[0]["ratio"] >= 2.0

    def test_normal_frequency_ok(self):
        trades = [_trade() for _ in range(3)]
        patterns = detect_overtrading(trades, baseline_monthly_count=3)
        assert len(patterns) == 0

    def test_zero_baseline_returns_empty(self):
        trades = [_trade()]
        patterns = detect_overtrading(trades, baseline_monthly_count=0)
        assert len(patterns) == 0


# --- Discipline Score ---

class TestDisciplineScore:
    def test_perfect_discipline(self):
        trades = [
            _trade(trade_type="buy", mosi_context={"readiness": {"status": "ready_now"}}),
            _trade(trade_type="buy", mosi_context={"readiness": {"status": "ready_now"}}),
        ]
        assert compute_discipline_score(trades) == 100.0

    def test_zero_discipline(self):
        trades = [
            _trade(trade_type="buy", mosi_context={"readiness": {"status": "not_ready"}}),
            _trade(trade_type="buy", mosi_context={"readiness": {"status": "getting_ready"}}),
        ]
        assert compute_discipline_score(trades) == 0.0

    def test_partial_discipline(self):
        trades = [
            _trade(trade_type="buy", mosi_context={"readiness": {"status": "ready_now"}}),
            _trade(trade_type="buy", mosi_context={"readiness": {"status": "not_ready"}}),
        ]
        assert compute_discipline_score(trades) == 50.0

    def test_no_buys_returns_zero(self):
        trades = [_trade(trade_type="sell")]
        assert compute_discipline_score(trades) == 0.0

    def test_sell_trades_excluded_from_score(self):
        trades = [
            _trade(trade_type="buy", mosi_context={"readiness": {"status": "ready_now"}}),
            _trade(trade_type="sell", mosi_context={"readiness": {"status": "not_ready"}}),
        ]
        assert compute_discipline_score(trades) == 100.0


# --- Learning Center ---

class TestLearningCenter:
    def test_all_courses_registered(self):
        courses = get_all_courses()
        assert len(courses) == 5
        titles = [c.title for c in courses]
        assert "MOSI 3-Layer Approach" in titles
        assert "Behavioral Discipline" in titles

    def test_courses_for_screener_dashboard(self):
        courses = get_courses_for_screen("screener_dashboard")
        assert len(courses) >= 1
        assert any(c.id == "mosi-3-layer" for c in courses)

    def test_courses_for_layer2_detail(self):
        courses = get_courses_for_screen("stock_detail_layer2")
        assert len(courses) >= 1
        assert any(c.id == "reading-ai-analysis" for c in courses)

    def test_courses_for_behavioral_report(self):
        courses = get_courses_for_screen("behavioral_report")
        assert any(c.id == "behavioral-discipline" for c in courses)

    def test_get_course_by_id_found(self):
        course = get_course_by_id("technical-rules")
        assert course is not None
        assert course.title == "Setting Technical Rules"

    def test_get_course_by_id_not_found(self):
        assert get_course_by_id("nonexistent") is None

    def test_no_courses_for_unknown_screen(self):
        assert get_courses_for_screen("unknown_screen") == []
