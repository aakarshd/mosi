import enum
from datetime import datetime, timezone, date

from sqlalchemy import ForeignKey, Enum, Boolean, Float, Date, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ModelType(str, enum.Enum):
    PASSIVE_INCOME = "passive_income"
    GROWTH = "growth"
    PE_EXPANSION = "pe_expansion"


class ScreenerResult(Base):
    __tablename__ = "screener_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    model_type: Mapped[ModelType] = mapped_column(Enum(ModelType))
    score: Mapped[float] = mapped_column(Float)
    qualified: Mapped[bool] = mapped_column(Boolean)
    criteria_json: Mapped[dict] = mapped_column(JSONB)
    run_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    stock: Mapped["Stock"] = relationship(back_populates="screener_results")

    __table_args__ = (
        Index("ix_screener_stock_model_date", "stock_id", "model_type", "run_date"),
    )
