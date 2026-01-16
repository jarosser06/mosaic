"""Reminder model for time-based notifications."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, EntityType, TimestampMixin
from .types import StringArray


class Reminder(Base, TimestampMixin):
    """Time-based notifications with optional recurrence and entity linking."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reminder_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[list[str]] = mapped_column(StringArray, default=list, nullable=False)
    recurrence_config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    related_entity_type: Mapped[Optional[EntityType]] = mapped_column(
        Enum(EntityType, native_enum=False)
    )
    related_entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_reminders_active", "reminder_time", "is_completed"),)
