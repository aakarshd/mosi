from fastapi import APIRouter, Depends, Query

from app.middleware.auth import get_current_user
from app.schemas.screener import ScreenerListResponse, ScreenerStockResponse
from app.utils.pagination import PaginationParams

router = APIRouter(tags=["screener"])


@router.get("/{model}", response_model=ScreenerListResponse)
async def list_screener_stocks(
    model: str,
    pagination: PaginationParams = Depends(),
    sort_by: str = Query("score", enum=["score", "name", "sector", "market_cap_category"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    sector: str | None = None,
    market_cap: str | None = None,
    user: dict = Depends(get_current_user),
):
    """List stocks qualifying for a screener model."""
    # TODO: Wire to database query
    return ScreenerListResponse(data=[], pagination={"page": pagination.page, "per_page": pagination.per_page, "total": 0, "pages": 0})


@router.get("/{model}/{stock_id}", response_model=ScreenerStockResponse)
async def get_screener_detail(
    model: str,
    stock_id: int,
    user: dict = Depends(get_current_user),
):
    """Get screener detail for a specific stock and model."""
    # TODO: Wire to database query
    raise NotImplementedError
