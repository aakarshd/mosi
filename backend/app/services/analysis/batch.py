"""Batch processing — runs Layer 2 analysis across all Layer 1 shortlisted stocks.

Triggered by: new quarterly data in document registry, or manual trigger.
Processes 200-500 stocks per cycle. Respects LLM budget ceiling.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.screener import ScreenerResult
from app.models.stock import Stock
from app.models.analysis import AnalysisCache
from app.services.analysis.adapters.base import LLMAdapter
from app.services.analysis.engine import analyze_stock
from app.services.documents.store import DocumentStore
from app.utils.datetime_helpers import format_quarter, utc_now

logger = logging.getLogger(__name__)

DEFAULT_MAX_COST_USD = 100.0  # Budget ceiling per batch cycle


async def run_batch_analysis(
    llm: LLMAdapter,
    doc_store: DocumentStore,
    max_stocks: int = 500,
    max_cost_usd: float = DEFAULT_MAX_COST_USD,
) -> dict:
    """Run Layer 2 analysis for all Layer 1 qualified stocks.

    Prioritizes stocks by Layer 1 ranking. Stops if budget ceiling reached.

    Returns:
        Summary dict with counts and costs.
    """
    db = SessionLocal()
    try:
        # Get qualified stocks (any model), ordered by screener score desc
        qualified = (
            db.query(Stock)
            .join(ScreenerResult)
            .filter(ScreenerResult.qualified == True)
            .distinct()
            .limit(max_stocks)
            .all()
        )

        current_quarter = format_quarter(utc_now())

        # Filter out stocks already analyzed this quarter
        stocks_to_analyze = []
        for stock in qualified:
            existing = db.query(AnalysisCache).filter(
                AnalysisCache.stock_id == stock.id,
                AnalysisCache.quarter_label == current_quarter,
            ).first()
            if existing is None:
                stocks_to_analyze.append(stock)

        logger.info(f"Batch analysis: {len(stocks_to_analyze)} stocks to analyze (of {len(qualified)} qualified)")

        stats = {"analyzed": 0, "failed": 0, "skipped_no_docs": 0, "total_cost_usd": 0.0, "budget_stopped": False}

        for stock in stocks_to_analyze:
            if stats["total_cost_usd"] >= max_cost_usd:
                logger.warning(f"Budget ceiling reached (${max_cost_usd}). Stopping batch.")
                stats["budget_stopped"] = True
                break

            result = await analyze_stock(stock, llm, doc_store, db)

            if result is None:
                # Check if it was a document issue or LLM issue
                if not doc_store.get_latest_documents(stock.isin):
                    stats["skipped_no_docs"] += 1
                else:
                    stats["failed"] += 1
            else:
                stats["analyzed"] += 1
                cost = result.analysis_json.get("llm_cost_usd", 0)
                stats["total_cost_usd"] += cost

        logger.info(f"Batch analysis complete: {stats}")
        return stats

    finally:
        db.close()
