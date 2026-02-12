from datetime import datetime, timezone, date, timedelta

import pytest

from app.utils.datetime_helpers import utc_now, to_ist, format_quarter, format_period, IST
from app.utils.validators import validate_stock_symbol, validate_model_type, validate_date_range
from app.utils.error_handlers import ValidationError
from app.utils.pagination import PaginationParams


# --- datetime_helpers ---

def test_utc_now_is_timezone_aware():
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_to_ist_converts_correctly():
    utc_dt = datetime(2026, 1, 15, 6, 0, 0, tzinfo=timezone.utc)
    ist_dt = to_ist(utc_dt)
    assert ist_dt.hour == 11
    assert ist_dt.minute == 30
    assert ist_dt.tzinfo == IST


def test_format_quarter_q1():
    dt = datetime(2026, 5, 15, tzinfo=timezone.utc)
    assert format_quarter(dt) == "Q1 FY26"


def test_format_quarter_q2():
    dt = datetime(2026, 8, 15, tzinfo=timezone.utc)
    assert format_quarter(dt) == "Q2 FY26"


def test_format_quarter_q3():
    dt = datetime(2026, 11, 15, tzinfo=timezone.utc)
    assert format_quarter(dt) == "Q3 FY26"


def test_format_quarter_q4():
    dt = datetime(2026, 2, 15, tzinfo=timezone.utc)
    assert format_quarter(dt) == "Q4 FY25"


def test_format_period():
    dt = datetime(2026, 3, 15, tzinfo=timezone.utc)
    assert format_period(dt) == "2026-03"


# --- validators ---

def test_validate_stock_symbol_valid():
    assert validate_stock_symbol("reliance") == "RELIANCE"
    assert validate_stock_symbol("  TCS  ") == "TCS"
    assert validate_stock_symbol("M&M") == "M&M"


def test_validate_stock_symbol_invalid():
    with pytest.raises(ValidationError):
        validate_stock_symbol("")
    with pytest.raises(ValidationError):
        validate_stock_symbol("123")
    with pytest.raises(ValidationError):
        validate_stock_symbol("a stock with spaces")


def test_validate_model_type_valid():
    assert validate_model_type("passive_income") == "passive_income"
    assert validate_model_type("GROWTH") == "growth"
    assert validate_model_type("  Pe_Expansion  ") == "pe_expansion"


def test_validate_model_type_invalid():
    with pytest.raises(ValidationError):
        validate_model_type("momentum")
    with pytest.raises(ValidationError):
        validate_model_type("")


def test_validate_date_range_valid():
    d1 = date(2026, 1, 1)
    d2 = date(2026, 3, 1)
    assert validate_date_range(d1, d2) == (d1, d2)


def test_validate_date_range_none():
    assert validate_date_range(None, None) == (None, None)


def test_validate_date_range_reversed():
    with pytest.raises(ValidationError):
        validate_date_range(date(2026, 3, 1), date(2026, 1, 1))


def test_validate_date_range_too_wide():
    with pytest.raises(ValidationError):
        validate_date_range(date(2025, 1, 1), date(2026, 6, 1))


# --- pagination ---

def test_pagination_defaults():
    p = PaginationParams()
    assert p.page == 1
    assert p.per_page == 20
    assert p.offset == 0


def test_pagination_offset():
    p = PaginationParams(page=3, per_page=10)
    assert p.offset == 20
