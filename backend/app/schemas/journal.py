from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class JournalCreateRequest(BaseModel):
    stock_id: int
    trade_type: str  # buy/sell/add
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    trade_date: date
    notes: str | None = None


class JournalEntryResponse(BaseModel):
    id: int
    stock_id: int
    symbol: str
    name: str
    trade_type: str
    quantity: int
    price: float
    trade_date: date
    auto_logged: bool
    mosi_context: dict | None
    notes: str | None
    created_at: datetime


class JournalListResponse(BaseModel):
    data: list[JournalEntryResponse]
    pagination: PaginationMeta


class BehavioralResponse(BaseModel):
    month_label: str
    discipline_score: float
    patterns: dict
    insights: str


class BehavioralHistoryResponse(BaseModel):
    data: list[BehavioralResponse]
