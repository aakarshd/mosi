import enum
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Boolean, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.screener import ModelType


class EntryRule(str, enum.Enum):
    BREAKOUT_VOLUME_MACD = "breakout_volume_macd"
    MACD_CONSOLIDATION_VOLUME = "macd_consolidation_volume"
    BREAKOUT_VOLUME = "breakout_volume"


class AdditionCap(str, enum.Enum):
    MAX_5_PCT = "max_5_pct"
    MAX_10_PCT = "max_10_pct"
    MAX_12_PCT = "max_12_pct"


class ExitRule(str, enum.Enum):
    EIGHT_PCT_DROP = "eight_pct_drop"
    MACD_RED = "macd_red"
    TRENDLINE_BREACH = "trendline_breach"


class SignalSource(str, enum.Enum):
    LAYER3 = "layer3"
    AARNA = "aarna"


class UserModelSelection(Base):
    __tablename__ = "user_model_selections"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    model_type: Mapped[ModelType] = mapped_column(Enum(ModelType))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "model_type", name="uq_user_model"),
    )


class UserTradingRules(Base):
    __tablename__ = "user_trading_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True)
    entry_rule: Mapped[EntryRule] = mapped_column(Enum(EntryRule), default=EntryRule.BREAKOUT_VOLUME_MACD)
    addition_cap: Mapped[AdditionCap] = mapped_column(Enum(AdditionCap), default=AdditionCap.MAX_5_PCT)
    exit_rule: Mapped[ExitRule] = mapped_column(Enum(ExitRule), default=ExitRule.EIGHT_PCT_DROP)
    signal_source: Mapped[SignalSource] = mapped_column(Enum(SignalSource), default=SignalSource.LAYER3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UserAlertPreferences(Base):
    __tablename__ = "user_alert_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True)
    channel_push: Mapped[bool] = mapped_column(Boolean, default=True)
    channel_email: Mapped[bool] = mapped_column(Boolean, default=False)
    channel_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    smart_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    frequency: Mapped[str] = mapped_column(Enum("immediate", "hourly_digest", "daily_digest", name="alert_frequency"), default="immediate")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
