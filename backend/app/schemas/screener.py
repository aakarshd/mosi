from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import PaginationMeta


class ScreenerCriteria(BaseModel):
    name: str
    passed: bool
    value: float | str | None = None
    threshold: float | str | None = None


class ScreenerStockResponse(BaseModel):
    stock_id: int
    symbol: str
    name: str
    sector: str | None
    market_cap_category: str | None
    model_type: str
    score: float
    qualified: bool
    criteria: list[ScreenerCriteria]
    run_date: date


class ScreenerListResponse(BaseModel):
    data: list[ScreenerStockResponse]
    pagination: PaginationMeta
