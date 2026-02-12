from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import PaginationMeta


class ScoreBreakdownResponse(BaseModel):
    layer1_contribution: float
    layer2_contribution: float
    signal_contribution: float
    total: float
    layer1_raw: float
    layer2_raw: float
    signal_raw: float


class ReadinessResponse(BaseModel):
    stock_id: int
    symbol: str
    name: str
    status: str
    mosi_score: float
    layer1_qualified: bool
    layer1_model: str
    layer2_verdict: str | None
    signal_source_result: dict | None
    status_changed_at: datetime


class ReadinessDetailResponse(BaseModel):
    stock_id: int
    symbol: str
    name: str
    status: str
    reason: str
    mosi_score: float
    score_breakdown: ScoreBreakdownResponse
    layer1_qualified: bool
    layer1_model: str
    layer2_verdict: str | None
    signal_source_result: dict | None
    status_changed_at: datetime


class ReadinessListResponse(BaseModel):
    data: list[ReadinessResponse]
    pagination: PaginationMeta


class TransitionResponse(BaseModel):
    from_status: str | None
    to_status: str
    reason: str | None
    transitioned_at: datetime


class TransitionListResponse(BaseModel):
    stock_id: int
    symbol: str
    transitions: list[TransitionResponse]
