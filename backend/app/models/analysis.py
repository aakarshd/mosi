import enum
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Enum, Float, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocType(str, enum.Enum):
    ANNUAL_REPORT = "annual_report"
    QUARTERLY_RESULTS = "quarterly_results"
    EARNINGS_TRANSCRIPT = "earnings_transcript"
    INVESTOR_PRESENTATION = "investor_presentation"


class DownloadStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADED = "downloaded"
    FAILED = "failed"


class Verdict(str, enum.Enum):
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    AVOID = "avoid"


class DocumentRegistry(Base):
    __tablename__ = "document_registry"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType))
    doc_url: Mapped[str] = mapped_column(Text)
    download_status: Mapped[DownloadStatus] = mapped_column(Enum(DownloadStatus), default=DownloadStatus.PENDING)
    file_path: Mapped[str | None] = mapped_column(Text)
    period_label: Mapped[str] = mapped_column(String(20))
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    stock: Mapped["Stock"] = relationship(back_populates="documents")


class AnalysisCache(Base):
    __tablename__ = "analysis_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    analysis_json: Mapped[dict] = mapped_column(JSONB)
    multi_bagger_score: Mapped[float] = mapped_column(Float)
    verdict: Mapped[Verdict] = mapped_column(Enum(Verdict))
    summary_text: Mapped[str] = mapped_column(Text)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    documents_used: Mapped[list] = mapped_column(JSONB)
    quarter_label: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    stock: Mapped["Stock"] = relationship(back_populates="analyses")

    __table_args__ = (
        UniqueConstraint("stock_id", "quarter_label", name="uq_analysis_stock_quarter"),
    )
