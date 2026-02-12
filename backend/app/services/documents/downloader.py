"""Throttled document downloader with retry logic.

Downloads PDFs from discovered URLs at a configurable rate.
Uses exponential backoff on failures. Immutable storage — never re-downloads
existing documents.
"""

import asyncio
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models.analysis import DocumentRegistry, DownloadStatus

logger = logging.getLogger(__name__)

DEFAULT_RATE_LIMIT = 10  # downloads per minute
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 2  # seconds


class DocumentDownloader:

    def __init__(
        self,
        storage_root: str = "/data/documents",
        rate_limit: int = DEFAULT_RATE_LIMIT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.storage_root = Path(storage_root)
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(rate_limit)
        self._delay = 60.0 / rate_limit  # seconds between downloads

    async def download_pending(self, db: Session) -> dict:
        """Download all pending documents from the registry.

        Returns: {"downloaded": N, "failed": N, "skipped": N}
        """
        pending = db.query(DocumentRegistry).filter(
            DocumentRegistry.download_status == DownloadStatus.PENDING
        ).all()

        logger.info(f"Processing {len(pending)} pending downloads")

        stats = {"downloaded": 0, "failed": 0, "skipped": 0}

        for doc in pending:
            # Check if file already exists (immutable — never re-download)
            dest = self._build_path(doc)
            if dest.exists():
                doc.download_status = DownloadStatus.DOWNLOADED
                doc.file_path = str(dest)
                stats["skipped"] += 1
                continue

            success = await self._download_with_retry(doc, dest)
            if success:
                doc.download_status = DownloadStatus.DOWNLOADED
                doc.file_path = str(dest)
                doc.downloaded_at = datetime.now(timezone.utc)
                stats["downloaded"] += 1
            else:
                doc.download_status = DownloadStatus.FAILED
                stats["failed"] += 1

            db.commit()
            await asyncio.sleep(self._delay)  # Throttle

        logger.info(f"Download batch complete: {stats}")
        return stats

    async def _download_with_retry(self, doc: DocumentRegistry, dest: Path) -> bool:
        """Download a single document with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                async with self._semaphore:
                    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                        response = await client.get(doc.doc_url, headers={"User-Agent": "MOSI/1.0"})
                        response.raise_for_status()

                        if "pdf" not in response.headers.get("content-type", "").lower() and not doc.doc_url.endswith(".pdf"):
                            logger.warning(f"Non-PDF response for {doc.doc_url}")
                            return False

                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(response.content)
                        logger.info(f"Downloaded: {doc.doc_url} -> {dest}")
                        return True

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                wait = DEFAULT_BACKOFF_BASE ** (attempt + 1)
                logger.warning(f"Download attempt {attempt + 1}/{self.max_retries} failed for {doc.doc_url}: {e}. Retrying in {wait}s")
                await asyncio.sleep(wait)

        logger.error(f"All retries exhausted for {doc.doc_url}")
        return False

    def _build_path(self, doc: DocumentRegistry) -> Path:
        """Build storage path: /{stock_isin}/{doc_type}/{hash}.pdf"""
        stock = doc.stock
        isin = stock.isin if stock else "unknown"
        url_hash = hashlib.md5(doc.doc_url.encode()).hexdigest()[:12]
        return self.storage_root / isin / doc.doc_type.value / f"{doc.period_label}_{url_hash}.pdf"
