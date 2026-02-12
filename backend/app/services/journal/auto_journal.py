"""Auto-journaling — captures trades from broker sync with MOSI context.

When a trade executes via the broker integration, this module creates a
journal entry enriched with the MOSI state at the time of trade:
model type, MOSI Score, AI verdict, Multi-Bagger Score, signal source.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.journal import TradeJournal, TradeType
from app.models.readiness import ReadinessStatus
from app.models.analysis import AnalysisCache
from app.models.screener import ScreenerResult

logger = logging.getLogger(__name__)


def capture_mosi_context(db: Session, user_id: str, stock_id: int) -> dict:
    """Snapshot the current MOSI state for a stock at trade time.

    This is stored as a historical record — the state at the moment
    the trade was executed, not the current live state.
    """
    context = {
        "captured_at": date.today().isoformat(),
        "layer1": {},
        "layer2": {},
        "readiness": {},
    }

    # Layer 1: latest qualifying screener result
    screener = (
        db.query(ScreenerResult)
        .filter(ScreenerResult.stock_id == stock_id, ScreenerResult.qualified.is_(True))
        .order_by(ScreenerResult.run_date.desc())
        .first()
    )
    if screener:
        context["layer1"] = {
            "model_type": screener.model_type.value,
            "score": screener.score,
            "qualified": True,
            "criteria": screener.criteria_json,
            "run_date": screener.run_date.isoformat(),
        }

    # Layer 2: latest analysis
    analysis = (
        db.query(AnalysisCache)
        .filter(AnalysisCache.stock_id == stock_id)
        .order_by(AnalysisCache.analyzed_at.desc())
        .first()
    )
    if analysis:
        context["layer2"] = {
            "verdict": analysis.verdict.value if analysis.verdict else None,
            "multi_bagger_score": analysis.analysis_json.get("multi_bagger_score", 0) if analysis.analysis_json else 0,
            "confidence": analysis.analysis_json.get("confidence_level", "Unknown") if analysis.analysis_json else "Unknown",
        }

    # Readiness at trade time
    readiness = (
        db.query(ReadinessStatus)
        .filter(ReadinessStatus.user_id == user_id, ReadinessStatus.stock_id == stock_id)
        .first()
    )
    if readiness:
        context["readiness"] = {
            "status": readiness.status.value,
            "mosi_score": readiness.mosi_score,
            "signal_source_result": readiness.signal_source_result,
        }

    return context


def log_trade(
    db: Session,
    user_id: str,
    stock_id: int,
    trade_type: str,
    quantity: int,
    price: float,
    trade_date: date,
    broker_order_id: str | None = None,
    notes: str | None = None,
    auto_logged: bool = False,
) -> TradeJournal:
    """Create a journal entry with MOSI context enrichment."""
    mosi_context = capture_mosi_context(db, user_id, stock_id)

    entry = TradeJournal(
        user_id=user_id,
        stock_id=stock_id,
        trade_type=TradeType(trade_type),
        quantity=quantity,
        price=price,
        trade_date=trade_date,
        auto_logged=auto_logged,
        broker_order_id=broker_order_id,
        mosi_context_json=mosi_context,
        notes_text=notes,
    )
    db.add(entry)
    db.commit()
    logger.info(f"Journal entry: {trade_type} {quantity}x @ {price} for stock {stock_id} (user: {user_id})")
    return entry


def on_broker_trade_event(db: Session, event: dict) -> TradeJournal:
    """Handle incoming broker trade event — auto-log to journal.

    Expected event format:
    {
        "user_id": str,
        "stock_id": int,
        "trade_type": "buy" | "sell" | "add",
        "quantity": int,
        "price": float,
        "trade_date": "YYYY-MM-DD",
        "order_id": str,
    }
    """
    return log_trade(
        db=db,
        user_id=event["user_id"],
        stock_id=event["stock_id"],
        trade_type=event["trade_type"],
        quantity=event["quantity"],
        price=event["price"],
        trade_date=date.fromisoformat(event["trade_date"]),
        broker_order_id=event.get("order_id"),
        auto_logged=True,
    )
