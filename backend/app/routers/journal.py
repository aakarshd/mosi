from datetime import date
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.journal import TradeJournal, BehavioralAnalysis
from app.models.stock import Stock
from app.schemas.journal import (
    JournalCreateRequest, JournalEntryResponse, JournalListResponse,
    BehavioralResponse, BehavioralHistoryResponse,
)
from app.services.journal.auto_journal import log_trade
from app.utils.pagination import PaginationParams
from app.utils.error_handlers import NotFoundError

router = APIRouter(tags=["journal"])


@router.get("/", response_model=JournalListResponse)
async def list_journal_entries(
    pagination: PaginationParams = Depends(),
    stock_id: int | None = None,
    trade_type: str | None = Query(None, enum=["buy", "sell", "add"]),
    date_from: date | None = None,
    date_to: date | None = None,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List trade journal entries with optional filters."""
    user_id = user.get("sub", "")

    query = (
        db.query(TradeJournal)
        .join(Stock)
        .filter(TradeJournal.user_id == user_id)
    )

    if stock_id:
        query = query.filter(TradeJournal.stock_id == stock_id)
    if trade_type:
        query = query.filter(TradeJournal.trade_type == trade_type)
    if date_from:
        query = query.filter(TradeJournal.trade_date >= date_from)
    if date_to:
        query = query.filter(TradeJournal.trade_date <= date_to)

    query = query.order_by(TradeJournal.trade_date.desc())

    total = query.count()
    entries = query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page).all()

    data = [
        JournalEntryResponse(
            id=e.id,
            stock_id=e.stock_id,
            symbol=e.stock.symbol,
            name=e.stock.name,
            trade_type=e.trade_type.value,
            quantity=e.quantity,
            price=e.price,
            trade_date=e.trade_date,
            auto_logged=e.auto_logged,
            mosi_context=e.mosi_context_json,
            notes=e.notes_text,
            created_at=e.created_at,
        )
        for e in entries
    ]

    return JournalListResponse(
        data=data,
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total, "pages": ceil(total / pagination.per_page) if pagination.per_page else 0},
    )


@router.post("/", response_model=JournalEntryResponse, status_code=201)
async def create_journal_entry(
    entry: JournalCreateRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a manual journal entry."""
    user_id = user.get("sub", "")

    journal = log_trade(
        db=db,
        user_id=user_id,
        stock_id=entry.stock_id,
        trade_type=entry.trade_type,
        quantity=entry.quantity,
        price=entry.price,
        trade_date=entry.trade_date,
        notes=entry.notes,
        auto_logged=False,
    )

    stock = db.query(Stock).filter(Stock.id == entry.stock_id).first()

    return JournalEntryResponse(
        id=journal.id,
        stock_id=journal.stock_id,
        symbol=stock.symbol if stock else "",
        name=stock.name if stock else "",
        trade_type=journal.trade_type.value,
        quantity=journal.quantity,
        price=journal.price,
        trade_date=journal.trade_date,
        auto_logged=journal.auto_logged,
        mosi_context=journal.mosi_context_json,
        notes=journal.notes_text,
        created_at=journal.created_at,
    )


@router.get("/behavioral", response_model=BehavioralResponse)
async def get_behavioral_report(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get latest monthly behavioral analysis report."""
    user_id = user.get("sub", "")
    report = (
        db.query(BehavioralAnalysis)
        .filter(BehavioralAnalysis.user_id == user_id)
        .order_by(BehavioralAnalysis.created_at.desc())
        .first()
    )
    if report is None:
        raise NotFoundError("No behavioral analysis available")

    return BehavioralResponse(
        month_label=report.month_label,
        discipline_score=report.discipline_score,
        patterns=report.patterns_json,
        insights=report.insights_text,
    )


@router.get("/behavioral/history", response_model=BehavioralHistoryResponse)
async def get_behavioral_history(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get historical discipline scores."""
    user_id = user.get("sub", "")
    reports = (
        db.query(BehavioralAnalysis)
        .filter(BehavioralAnalysis.user_id == user_id)
        .order_by(BehavioralAnalysis.created_at.desc())
        .limit(12)  # Last 12 months
        .all()
    )

    return BehavioralHistoryResponse(data=[
        BehavioralResponse(
            month_label=r.month_label,
            discipline_score=r.discipline_score,
            patterns=r.patterns_json,
            insights=r.insights_text,
        )
        for r in reports
    ])
