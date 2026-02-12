from fastapi import APIRouter, Depends, Query

from app.middleware.auth import get_current_user
from app.schemas.readiness import ReadinessListResponse, ReadinessResponse, TransitionListResponse
from app.utils.pagination import PaginationParams

router = APIRouter(tags=["readiness"])


@router.get("/", response_model=ReadinessListResponse)
async def list_readiness(
    pagination: PaginationParams = Depends(),
    status: str | None = Query(None, enum=["ready_now", "getting_ready", "not_ready", "exit_alert"]),
    model: str | None = None,
    sort_by: str = Query("mosi_score", enum=["mosi_score", "status_changed_at", "symbol"]),
    user: dict = Depends(get_current_user),
):
    """List all stocks with readiness status for current user."""
    # TODO: Wire to database query
    return ReadinessListResponse(data=[], pagination={"page": pagination.page, "per_page": pagination.per_page, "total": 0, "pages": 0})


@router.get("/{stock_id}", response_model=ReadinessResponse)
async def get_readiness_detail(
    stock_id: int,
    user: dict = Depends(get_current_user),
):
    """Get detailed readiness breakdown — Layer 1 + Layer 2 + signal source."""
    # TODO: Wire to database query
    raise NotImplementedError


@router.get("/transitions/{stock_id}", response_model=TransitionListResponse)
async def get_transitions(
    stock_id: int,
    user: dict = Depends(get_current_user),
):
    """Get status transition history for a stock."""
    # TODO: Wire to database query
    raise NotImplementedError
