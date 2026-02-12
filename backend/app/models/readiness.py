import enum
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Float, Enum, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.screener import ModelType
from app.models.analysis import Verdict


class ReadinessLevel(str, enum.Enum):
    READY_NOW = "ready_now"
    GETTING_READY = "getting_ready"
    NOT_READY = "not_ready"
    EXIT_ALERT = "exit_alert"


class ReadinessStatus(Base):
    __tablename__ = "readiness_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    status: Mapped[ReadinessLevel] = mapped_column(Enum(ReadinessLevel))
    mosi_score: Mapped[float] = mapped_column(Float)
    layer1_qualified: Mapped[bool] = mapped_column()
    layer1_model: Mapped[ModelType] = mapped_column(Enum(ModelType))
    layer2_verdict: Mapped[Verdict | None] = mapped_column(Enum(Verdict))
    signal_source_result: Mapped[dict | None] = mapped_column(JSONB)
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    stock: Mapped["Stock"] = relationship(back_populates="readiness_statuses")
    transitions: Mapped[list["StatusTransition"]] = relationship(back_populates="readiness_status")

    __table_args__ = (
        UniqueConstraint("user_id", "stock_id", name="uq_user_stock_readiness"),
        Index("ix_readiness_user_status", "user_id", "status"),
    )


class StatusTransition(Base):
    __tablename__ = "status_transitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    readiness_status_id: Mapped[int] = mapped_column(ForeignKey("readiness_status.id"), index=True)
    from_status: Mapped[ReadinessLevel | None] = mapped_column(Enum(ReadinessLevel))
    to_status: Mapped[ReadinessLevel] = mapped_column(Enum(ReadinessLevel))
    reason_text: Mapped[str | None] = mapped_column(Text)
    transitioned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    readiness_status: Mapped["ReadinessStatus"] = relationship(back_populates="transitions")
