from datetime import date

from fastapi import APIRouter, Depends, Query

from app.middleware.auth import get_current_user
from app.schemas.journal import JournalCreateRequest, JournalEntryResponse, JournalListResponse, BehavioralResponse, BehavioralHistoryResponse
from app.utils.pagination import PaginationParams

router = APIRouter(tags=["journal"])


@router.get("/", response_model=JournalListResponse)
async def list_journal_entries(
    pagination: PaginationParams = Depends(),
    stock_id: int | None = None,
    trade_type: str | None = Query(None, enum=["buy", "sell", "add"]),
    date_from: date | None = None,
    date_to: date | None = None,
    user: dict = Depends(get_current_user),
):
    """List trade journal entries with optional filters."""
    # TODO: Wire to database query
    return JournalListResponse(data=[], pagination={"page": pagination.page, "per_page": pagination.per_page, "total": 0, "pages": 0})


@router.post("/", response_model=JournalEntryResponse, status_code=201)
async def create_journal_entry(
    entry: JournalCreateRequest,
    user: dict = Depends(get_current_user),
):
    """Create a manual journal entry."""
    # TODO: Wire to database insert
    raise NotImplementedError


@router.get("/behavioral", response_model=BehavioralResponse)
async def get_behavioral_report(
    user: dict = Depends(get_current_user),
):
    """Get latest monthly behavioral analysis report."""
    # TODO: Wire to database query
    raise NotImplementedError


@router.get("/behavioral/history", response_model=BehavioralHistoryResponse)
async def get_behavioral_history(
    user: dict = Depends(get_current_user),
):
    """Get historical discipline scores."""
    # TODO: Wire to database query
    return BehavioralHistoryResponse(data=[])
