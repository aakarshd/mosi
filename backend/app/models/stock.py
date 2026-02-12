import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Enum, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Exchange(str, enum.Enum):
    NSE = "NSE"
    BSE = "BSE"


class MarketCapCategory(str, enum.Enum):
    LARGE = "large"
    MID = "mid"
    SMALL = "small"


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    isin: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[Exchange] = mapped_column(Enum(Exchange))
    sector: Mapped[str | None] = mapped_column(String(100))
    market_cap_category: Mapped[MarketCapCategory | None] = mapped_column(Enum(MarketCapCategory))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    screener_results: Mapped[list["ScreenerResult"]] = relationship(back_populates="stock")
    documents: Mapped[list["DocumentRegistry"]] = relationship(back_populates="stock")
    analyses: Mapped[list["AnalysisCache"]] = relationship(back_populates="stock")
    readiness_statuses: Mapped[list["ReadinessStatus"]] = relationship(back_populates="stock")
    journal_entries: Mapped[list["TradeJournal"]] = relationship(back_populates="stock")

    __table_args__ = (
        Index("ix_stocks_sector", "sector"),
        Index("ix_stocks_market_cap", "market_cap_category"),
    )
