from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.sebi_disclaimer import inject_disclaimer
from app.models.screener import ScreenerResult, ModelType
from app.models.stock import Stock
from app.schemas.screener import ScreenerListResponse, ScreenerStockResponse
from app.utils.pagination import PaginationParams
from app.utils.error_handlers import NotFoundError

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
    db: Session = Depends(get_db),
):
    """List stocks qualifying for a screener model."""
    model_type = ModelType(model)

    query = (
        db.query(ScreenerResult)
        .join(Stock)
        .filter(ScreenerResult.model_type == model_type, ScreenerResult.qualified.is_(True))
    )

    if sector:
        query = query.filter(Stock.sector == sector)
    if market_cap:
        query = query.filter(Stock.market_cap_category == market_cap)

    sort_col = {
        "score": ScreenerResult.score,
        "name": Stock.name,
        "sector": Stock.sector,
        "market_cap_category": Stock.market_cap_category,
    }.get(sort_by, ScreenerResult.score)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    total = query.count()
    results = query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page).all()

    data = []
    for r in results:
        criteria = [
            {"name": k, "passed": v.get("passed"), "value": v.get("value"), "threshold": v.get("threshold")}
            for k, v in (r.criteria_json or {}).items()
        ]
        data.append(ScreenerStockResponse(
            stock_id=r.stock_id,
            symbol=r.stock.symbol,
            name=r.stock.name,
            sector=r.stock.sector,
            market_cap_category=r.stock.market_cap_category.value if r.stock.market_cap_category else None,
            model_type=r.model_type.value,
            score=r.score,
            qualified=r.qualified,
            criteria=criteria,
            run_date=r.run_date,
        ))

    return ScreenerListResponse(
        data=data,
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total, "pages": ceil(total / pagination.per_page) if pagination.per_page else 0},
    )


@router.get("/{model}/{stock_id}", response_model=ScreenerStockResponse)
async def get_screener_detail(
    model: str,
    stock_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get screener detail for a specific stock and model."""
    model_type = ModelType(model)
    result = (
        db.query(ScreenerResult)
        .join(Stock)
        .filter(ScreenerResult.stock_id == stock_id, ScreenerResult.model_type == model_type)
        .order_by(ScreenerResult.run_date.desc())
        .first()
    )
    if result is None:
        raise NotFoundError(f"No screener result for stock {stock_id} model {model}")

    criteria = [
        {"name": k, "passed": v.get("passed"), "value": v.get("value"), "threshold": v.get("threshold")}
        for k, v in (result.criteria_json or {}).items()
    ]
    return ScreenerStockResponse(
        stock_id=result.stock_id,
        symbol=result.stock.symbol,
        name=result.stock.name,
        sector=result.stock.sector,
        market_cap_category=result.stock.market_cap_category.value if result.stock.market_cap_category else None,
        model_type=result.model_type.value,
        score=result.score,
        qualified=result.qualified,
        criteria=criteria,
        run_date=result.run_date,
    )
