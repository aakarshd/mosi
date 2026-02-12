import re
from datetime import date, timedelta

from app.utils.error_handlers import ValidationError

VALID_MODELS = {"passive_income", "growth", "pe_expansion"}
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9&\-]{0,19}$")
MAX_DATE_RANGE_DAYS = 365


def validate_stock_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(f"Invalid stock symbol: '{symbol}'. Must be uppercase alphanumeric (NSE/BSE format).")
    return symbol


def validate_model_type(model: str) -> str:
    model = model.strip().lower()
    if model not in VALID_MODELS:
        raise ValidationError(f"Invalid model type: '{model}'. Must be one of: {', '.join(sorted(VALID_MODELS))}")
    return model


def validate_date_range(date_from: date | None, date_to: date | None) -> tuple[date | None, date | None]:
    if date_from is None and date_to is None:
        return None, None
    if date_from and date_to:
        if date_from > date_to:
            raise ValidationError("date_from must be before date_to")
        if (date_to - date_from).days > MAX_DATE_RANGE_DAYS:
            raise ValidationError(f"Date range cannot exceed {MAX_DATE_RANGE_DAYS} days")
    return date_from, date_to
