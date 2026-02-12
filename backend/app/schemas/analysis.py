from datetime import datetime

from pydantic import BaseModel


class AnalysisPoint(BaseModel):
    point_number: int
    title: str
    finding: str
    score: float | None = None
    evidence: list[str] = []


class AnalysisResponse(BaseModel):
    stock_id: int
    symbol: str
    name: str
    points: list[AnalysisPoint]
    multi_bagger_score: float
    verdict: str
    summary: str
    quarter_label: str
    analyzed_at: datetime
    documents_used: list[str]


class AnalysisSummaryResponse(BaseModel):
    stock_id: int
    symbol: str
    name: str
    multi_bagger_score: float
    verdict: str
    summary: str
    quarter_label: str
    analyzed_at: datetime
