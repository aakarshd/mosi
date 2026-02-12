from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

# NSE market holidays for 2026 (gazetted)
MARKET_HOLIDAYS_2026 = {
    "2026-01-26",  # Republic Day
    "2026-03-10",  # Maha Shivaratri
    "2026-03-17",  # Holi
    "2026-03-31",  # Id-Ul-Fitr
    "2026-04-02",  # Ram Navami
    "2026-04-03",  # Mahavir Jayanti
    "2026-04-14",  # Dr. Ambedkar Jayanti
    "2026-04-18",  # Good Friday
    "2026-05-01",  # Maharashtra Day
    "2026-06-07",  # Id-Ul-Adha (Bakri Id)
    "2026-07-07",  # Muharram
    "2026-08-15",  # Independence Day
    "2026-08-26",  # Janmashtami
    "2026-09-05",  # Milad-Un-Nabi
    "2026-10-02",  # Mahatma Gandhi Jayanti
    "2026-10-20",  # Dussehra
    "2026-11-09",  # Diwali (Laxmi Pujan)
    "2026-11-10",  # Diwali (Balipratipada)
    "2026-11-30",  # Guru Nanak Jayanti
    "2026-12-25",  # Christmas
}

MARKET_OPEN = (9, 15)   # 9:15 AM IST
MARKET_CLOSE = (15, 30)  # 3:30 PM IST


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_ist(dt: datetime) -> datetime:
    return dt.astimezone(IST)


def market_hours_active() -> bool:
    now_ist = to_ist(utc_now())
    date_str = now_ist.strftime("%Y-%m-%d")
    if date_str in MARKET_HOLIDAYS_2026:
        return False
    if now_ist.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    current_minutes = now_ist.hour * 60 + now_ist.minute
    open_minutes = MARKET_OPEN[0] * 60 + MARKET_OPEN[1]
    close_minutes = MARKET_CLOSE[0] * 60 + MARKET_CLOSE[1]
    return open_minutes <= current_minutes <= close_minutes


def format_quarter(dt: datetime) -> str:
    month = dt.month
    year = dt.year
    if month <= 3:
        return f"Q4 FY{str(year - 1)[2:]}"
    elif month <= 6:
        return f"Q1 FY{str(year)[2:]}"
    elif month <= 9:
        return f"Q2 FY{str(year)[2:]}"
    else:
        return f"Q3 FY{str(year)[2:]}"


def format_period(dt: datetime) -> str:
    return dt.strftime("%Y-%m")
