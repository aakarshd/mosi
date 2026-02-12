from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.readiness import ReadinessStatus
from app.models.stock import Stock
from app.models.user_config import UserTradingRules
from app.schemas.portfolio import (
    PortfolioResponse, PortfolioMetricsResponse, ComplianceResponse,
    HoldingResponse, AllocationBreakdown,
)
from app.utils.error_handlers import NotFoundError

router = APIRouter(tags=["portfolio"])


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's portfolio with compliance badges.

    Portfolio data comes from broker integration. This endpoint joins
    broker positions with MOSI readiness data to provide compliance tracking.
    """
    user_id = user.get("sub", "")

    # Readiness data for all user's tracked stocks
    readiness_records = (
        db.query(ReadinessStatus)
        .join(Stock)
        .filter(ReadinessStatus.user_id == user_id)
        .all()
    )

    holdings = []
    sector_map: dict[str, float] = {}
    mcap_map: dict[str, float] = {}
    model_map: dict[str, float] = {}
    total_value = 0.0

    for r in readiness_records:
        # Placeholder: real portfolio data would come from broker sync
        # For now, display tracked stocks with readiness data
        holding = HoldingResponse(
            stock_id=r.stock_id,
            symbol=r.stock.symbol,
            name=r.stock.name,
            quantity=0,
            avg_price=0.0,
            current_price=None,
            mosi_score=r.mosi_score,
            compliance_status="following_rules" if r.status.value in ("ready_now", "getting_ready") else "deviated",
            deviation_reasons=_get_deviation_reasons(r),
        )
        holdings.append(holding)

        sector = r.stock.sector or "Unknown"
        sector_map[sector] = sector_map.get(sector, 0) + 1
        mcap = r.stock.market_cap_category.value if r.stock.market_cap_category else "unknown"
        mcap_map[mcap] = mcap_map.get(mcap, 0) + 1
        model_label = r.layer1_model.value if r.layer1_model else "none"
        model_map[model_label] = model_map.get(model_label, 0) + 1

    total_stocks = max(len(holdings), 1)
    compliance_count = sum(1 for h in holdings if h.compliance_status == "following_rules")
    mosi_scores = [h.mosi_score for h in holdings if h.mosi_score]

    metrics = PortfolioMetricsResponse(
        weighted_mosi_score=sum(mosi_scores) / len(mosi_scores) if mosi_scores else 0,
        compliance_rate=compliance_count / total_stocks * 100,
        total_holdings=len(holdings),
        sector_allocation=[
            AllocationBreakdown(label=k, percentage=v / total_stocks * 100, value=v)
            for k, v in sector_map.items()
        ],
        market_cap_allocation=[
            AllocationBreakdown(label=k, percentage=v / total_stocks * 100, value=v)
            for k, v in mcap_map.items()
        ],
        model_allocation=[
            AllocationBreakdown(label=k, percentage=v / total_stocks * 100, value=v)
            for k, v in model_map.items()
        ],
    )

    return PortfolioResponse(holdings=holdings, metrics=metrics)


@router.get("/metrics", response_model=PortfolioMetricsResponse)
async def get_portfolio_metrics(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get portfolio-level metrics — weighted MOSI score, compliance rate, allocations."""
    portfolio = await get_portfolio(user=user, db=db)
    return portfolio.metrics


@router.get("/{stock_id}/compliance", response_model=ComplianceResponse)
async def get_compliance_detail(
    stock_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get compliance detail for a specific holding."""
    user_id = user.get("sub", "")
    readiness = (
        db.query(ReadinessStatus)
        .join(Stock)
        .filter(ReadinessStatus.user_id == user_id, ReadinessStatus.stock_id == stock_id)
        .first()
    )
    if readiness is None:
        raise NotFoundError(f"No readiness data for stock {stock_id}")

    # Check trading rules compliance
    rules = db.query(UserTradingRules).filter(UserTradingRules.user_id == user_id).first()

    ai_verdict_aligned = readiness.layer2_verdict is not None and readiness.layer2_verdict.value in ("buy", "hold")

    return ComplianceResponse(
        stock_id=stock_id,
        symbol=readiness.stock.symbol,
        entry_range_ok=readiness.status.value in ("ready_now", "getting_ready"),
        stop_loss_present=rules is not None,
        position_size_ok=True,  # Real check requires broker position data
        ai_verdict_aligned=ai_verdict_aligned,
        overall_status="following_rules" if readiness.status.value in ("ready_now", "getting_ready") else "deviated",
        details={
            "readiness_status": readiness.status.value,
            "mosi_score": readiness.mosi_score,
            "exit_rule": rules.exit_rule.value if rules else "eight_pct_drop",
        },
    )


def _get_deviation_reasons(readiness: ReadinessStatus) -> list[str]:
    """Get reasons why a holding deviates from MOSI rules."""
    reasons = []
    if readiness.status.value == "exit_alert":
        reasons.append("Exit signal triggered — consider selling")
    if readiness.status.value == "not_ready":
        reasons.append("Stock no longer qualifies across all 3 layers")
    if readiness.layer2_verdict and readiness.layer2_verdict.value == "avoid":
        reasons.append("AI verdict is Avoid")
    return reasons
