from pydantic import BaseModel


class HoldingResponse(BaseModel):
    stock_id: int
    symbol: str
    name: str
    quantity: int
    avg_price: float
    current_price: float | None
    mosi_score: float | None
    compliance_status: str  # "following_rules" | "deviated"
    deviation_reasons: list[str] = []


class AllocationBreakdown(BaseModel):
    label: str
    percentage: float
    value: float


class PortfolioMetricsResponse(BaseModel):
    weighted_mosi_score: float
    compliance_rate: float
    total_holdings: int
    sector_allocation: list[AllocationBreakdown]
    market_cap_allocation: list[AllocationBreakdown]
    model_allocation: list[AllocationBreakdown]


class PortfolioResponse(BaseModel):
    holdings: list[HoldingResponse]
    metrics: PortfolioMetricsResponse


class ComplianceResponse(BaseModel):
    stock_id: int
    symbol: str
    entry_range_ok: bool
    stop_loss_present: bool
    position_size_ok: bool
    ai_verdict_aligned: bool
    overall_status: str
    details: dict
