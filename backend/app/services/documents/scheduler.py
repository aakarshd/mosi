"""Document discovery and download scheduler.

- URL discovery: weekly cron + event-triggered on BSE announcements
- Download: runs after URL discovery to fetch pending documents
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.analysis import DocumentRegistry, DownloadStatus, DocType
from app.models.screener import ScreenerResult
from app.services.documents.bse_scraper import discover_document_urls
from app.services.documents.downloader import DocumentDownloader

logger = logging.getLogger(__name__)


async def run_url_discovery(db: Session) -> dict:
    """Discover document URLs for all Layer 1 qualified stocks.

    Returns: {"stocks_processed": N, "urls_discovered": N, "new_urls": N}
    """
    # Get unique stock IDs that qualified in any model's latest run
    qualified_stocks = (
        db.query(ScreenerResult.stock_id, ScreenerResult.stock)
        .filter(ScreenerResult.qualified == True)
        .distinct(ScreenerResult.stock_id)
        .all()
    )

    logger.info(f"Running URL discovery for {len(qualified_stocks)} qualified stocks")

    total_discovered = 0
    new_urls = 0

    for stock_id, stock in qualified_stocks:
        # Use ISIN as BSE scrip code lookup (simplified — real impl needs scrip code mapping)
        docs = await discover_document_urls(stock.isin)

        for doc in docs:
            # Check if URL already in registry
            exists = db.query(DocumentRegistry).filter(
                DocumentRegistry.doc_url == doc["doc_url"]
            ).first()

            if exists:
                continue

            registry_entry = DocumentRegistry(
                stock_id=stock_id,
                doc_type=DocType(doc["doc_type"]),
                doc_url=doc["doc_url"],
                download_status=DownloadStatus.PENDING,
                period_label=doc["period_label"],
            )
            db.add(registry_entry)
            new_urls += 1

        total_discovered += len(docs)

    db.commit()
    result = {"stocks_processed": len(qualified_stocks), "urls_discovered": total_discovered, "new_urls": new_urls}
    logger.info(f"URL discovery complete: {result}")
    return result


async def run_download_batch(storage_root: str = "/data/documents") -> dict:
    """Download all pending documents."""
    db = SessionLocal()
    try:
        downloader = DocumentDownloader(storage_root=storage_root)
        return await downloader.download_pending(db)
    finally:
        db.close()


async def run_full_pipeline(storage_root: str = "/data/documents") -> dict:
    """Run full document pipeline: discover URLs then download."""
    db = SessionLocal()
    try:
        discovery_result = await run_url_discovery(db)
    finally:
        db.close()

    download_result = await run_download_batch(storage_root)
    return {"discovery": discovery_result, "download": download_result}
