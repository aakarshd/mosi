from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from app.schemas.portfolio import PortfolioResponse, PortfolioMetricsResponse, ComplianceResponse

router = APIRouter(tags=["portfolio"])


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(
    user: dict = Depends(get_current_user),
):
    """Get user's portfolio with compliance badges."""
    # TODO: Wire to broker integration + database
    raise NotImplementedError


@router.get("/metrics", response_model=PortfolioMetricsResponse)
async def get_portfolio_metrics(
    user: dict = Depends(get_current_user),
):
    """Get portfolio-level metrics — weighted MOSI score, compliance rate, allocations."""
    # TODO: Wire to database
    raise NotImplementedError


@router.get("/{stock_id}/compliance", response_model=ComplianceResponse)
async def get_compliance_detail(
    stock_id: int,
    user: dict = Depends(get_current_user),
):
    """Get compliance detail for a specific holding."""
    # TODO: Wire to database
    raise NotImplementedError
