"""ActionItem model for task management."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import ActionItemStatus, Base, EntityType, PrivacyLevel, TimestampMixin
from .types import StringArray


class ActionItem(Base, TimestampMixin):
    """Task management with status tracking and optional entity associations."""

    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(5000))
    status: Mapped[ActionItemStatus] = mapped_column(
        Enum(ActionItemStatus, native_enum=False),
        default=ActionItemStatus.PENDING,
        nullable=False,
        index=True,
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    entity_type: Mapped[Optional[EntityType]] = mapped_column(Enum(EntityType, native_enum=False))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    privacy_level: Mapped[PrivacyLevel] = mapped_column(
        Enum(PrivacyLevel, native_enum=False),
        default=PrivacyLevel.PRIVATE,
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(
        StringArray, default=list, nullable=False, server_default="{}"
    )

    __table_args__ = (
        Index("ix_action_items_entity", "entity_type", "entity_id"),
        Index("ix_action_items_status_due_date", "status", "due_date"),
    )
