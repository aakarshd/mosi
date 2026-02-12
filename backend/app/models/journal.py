import enum
from datetime import datetime, timezone, date

from sqlalchemy import ForeignKey, String, Integer, Float, Boolean, Enum, Text, Date, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TradeType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    ADD = "add"


class TradeJournal(Base):
    __tablename__ = "trade_journal"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    trade_type: Mapped[TradeType] = mapped_column(Enum(TradeType))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    trade_date: Mapped[date] = mapped_column(Date)
    auto_logged: Mapped[bool] = mapped_column(Boolean, default=False)
    broker_order_id: Mapped[str | None] = mapped_column(String(100))
    mosi_context_json: Mapped[dict | None] = mapped_column(JSONB)
    notes_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    stock: Mapped["Stock"] = relationship(back_populates="journal_entries")


class BehavioralAnalysis(Base):
    __tablename__ = "behavioral_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    month_label: Mapped[str] = mapped_column(String(10))
    discipline_score: Mapped[float] = mapped_column(Float)
    patterns_json: Mapped[dict] = mapped_column(JSONB)
    insights_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "month_label", name="uq_user_month_behavioral"),
    )
