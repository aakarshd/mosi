from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.readiness import ReadinessStatus, ReadinessLevel, StatusTransition
from app.models.stock import Stock
from app.schemas.readiness import ReadinessListResponse, ReadinessResponse, ReadinessDetailResponse, ScoreBreakdownResponse, TransitionListResponse, TransitionResponse
from app.utils.pagination import PaginationParams
from app.utils.error_handlers import NotFoundError

router = APIRouter(tags=["readiness"])


@router.get("/", response_model=ReadinessListResponse)
async def list_readiness(
    pagination: PaginationParams = Depends(),
    status: str | None = Query(None, enum=["ready_now", "getting_ready", "not_ready", "exit_alert"]),
    model: str | None = None,
    sort_by: str = Query("mosi_score", enum=["mosi_score", "status_changed_at", "symbol"]),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all stocks with readiness status for current user."""
    user_id = user.get("sub", "")

    query = (
        db.query(ReadinessStatus)
        .join(Stock)
        .filter(ReadinessStatus.user_id == user_id)
    )

    if status:
        query = query.filter(ReadinessStatus.status == ReadinessLevel(status))
    if model:
        from app.models.screener import ModelType
        query = query.filter(ReadinessStatus.layer1_model == ModelType(model))

    sort_col = {
        "mosi_score": ReadinessStatus.mosi_score.desc(),
        "status_changed_at": ReadinessStatus.status_changed_at.desc(),
        "symbol": Stock.symbol.asc(),
    }.get(sort_by, ReadinessStatus.mosi_score.desc())
    query = query.order_by(sort_col)

    total = query.count()
    results = query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page).all()

    data = [
        ReadinessResponse(
            stock_id=r.stock_id,
            symbol=r.stock.symbol,
            name=r.stock.name,
            status=r.status.value,
            mosi_score=r.mosi_score,
            layer1_qualified=r.layer1_qualified,
            layer1_model=r.layer1_model.value if r.layer1_model else "",
            layer2_verdict=r.layer2_verdict.value if r.layer2_verdict else None,
            signal_source_result=r.signal_source_result,
            status_changed_at=r.status_changed_at,
        )
        for r in results
    ]

    return ReadinessListResponse(
        data=data,
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total, "pages": ceil(total / pagination.per_page) if pagination.per_page else 0},
    )


@router.get("/{stock_id}", response_model=ReadinessDetailResponse)
async def get_readiness_detail(
    stock_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed readiness breakdown — Layer 1 + Layer 2 + signal source."""
    user_id = user.get("sub", "")
    result = (
        db.query(ReadinessStatus)
        .join(Stock)
        .filter(ReadinessStatus.user_id == user_id, ReadinessStatus.stock_id == stock_id)
        .first()
    )
    if result is None:
        raise NotFoundError(f"No readiness data for stock {stock_id}")

    # Compute score breakdown from stored MOSI score (approximate reconstruction)
    score_third = result.mosi_score / 3
    breakdown = ScoreBreakdownResponse(
        layer1_contribution=score_third if result.layer1_qualified else 0,
        layer2_contribution=score_third if result.layer2_verdict else 0,
        signal_contribution=score_third,
        total=result.mosi_score,
        layer1_raw=100.0 if result.layer1_qualified else 0,
        layer2_raw=0,
        signal_raw=0,
    )

    return ReadinessDetailResponse(
        stock_id=result.stock_id,
        symbol=result.stock.symbol,
        name=result.stock.name,
        status=result.status.value,
        reason="",
        mosi_score=result.mosi_score,
        score_breakdown=breakdown,
        layer1_qualified=result.layer1_qualified,
        layer1_model=result.layer1_model.value if result.layer1_model else "",
        layer2_verdict=result.layer2_verdict.value if result.layer2_verdict else None,
        signal_source_result=result.signal_source_result,
        status_changed_at=result.status_changed_at,
    )


@router.get("/transitions/{stock_id}", response_model=TransitionListResponse)
async def get_transitions(
    stock_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get status transition history for a stock."""
    user_id = user.get("sub", "")
    readiness = (
        db.query(ReadinessStatus)
        .filter(ReadinessStatus.user_id == user_id, ReadinessStatus.stock_id == stock_id)
        .first()
    )
    if readiness is None:
        raise NotFoundError(f"No readiness data for stock {stock_id}")

    transitions = (
        db.query(StatusTransition)
        .filter(StatusTransition.readiness_status_id == readiness.id)
        .order_by(StatusTransition.transitioned_at.desc())
        .all()
    )

    stock = db.query(Stock).filter(Stock.id == stock_id).first()

    return TransitionListResponse(
        stock_id=stock_id,
        symbol=stock.symbol if stock else "",
        transitions=[
            TransitionResponse(
                from_status=t.from_status.value if t.from_status else None,
                to_status=t.to_status.value,
                reason=t.reason_text,
                transitioned_at=t.transitioned_at,
            )
            for t in transitions
        ],
    )
