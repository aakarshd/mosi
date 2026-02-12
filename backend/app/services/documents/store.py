"""Document store — manages local storage of downloaded PDFs.

Immutable, append-only storage organized by stock ISIN, document type, and period.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentStore:

    def __init__(self, storage_root: str = "/data/documents"):
        self.root = Path(storage_root)

    def get_documents_for_stock(self, isin: str) -> list[dict]:
        """List all downloaded documents for a stock."""
        stock_dir = self.root / isin
        if not stock_dir.exists():
            return []

        docs = []
        for doc_type_dir in stock_dir.iterdir():
            if not doc_type_dir.is_dir():
                continue
            for pdf in doc_type_dir.glob("*.pdf"):
                docs.append({
                    "isin": isin,
                    "doc_type": doc_type_dir.name,
                    "filename": pdf.name,
                    "path": str(pdf),
                    "size_bytes": pdf.stat().st_size,
                })

        return docs

    def get_document_path(self, isin: str, doc_type: str, filename: str) -> Path | None:
        """Get the full path to a specific document."""
        path = self.root / isin / doc_type / filename
        return path if path.exists() else None

    def get_latest_documents(self, isin: str, doc_types: list[str] | None = None) -> list[Path]:
        """Get the most recent document of each type for a stock.

        Used by Layer 2 AI analysis to feed documents to the LLM.
        """
        stock_dir = self.root / isin
        if not stock_dir.exists():
            return []

        latest = []
        target_types = doc_types or ["annual_report", "quarterly_results", "earnings_transcript", "investor_presentation"]

        for dtype in target_types:
            type_dir = stock_dir / dtype
            if not type_dir.exists():
                continue
            pdfs = sorted(type_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
            if pdfs:
                latest.append(pdfs[0])

        return latest

    def stats(self) -> dict:
        """Get storage statistics."""
        total_stocks = 0
        total_docs = 0
        total_size = 0

        if not self.root.exists():
            return {"stocks": 0, "documents": 0, "size_bytes": 0}

        for stock_dir in self.root.iterdir():
            if not stock_dir.is_dir():
                continue
            total_stocks += 1
            for pdf in stock_dir.rglob("*.pdf"):
                total_docs += 1
                total_size += pdf.stat().st_size

        return {"stocks": total_stocks, "documents": total_docs, "size_bytes": total_size}
