"""Work session model for time tracking."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PrivacyLevel, TimestampMixin
from .types import StringArray

if TYPE_CHECKING:
    from datetime import date  # noqa: F401

    from .project import Project


class WorkSession(Base, TimestampMixin):
    """Individual time entries for project work with direct duration input."""

    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # noqa: F811
    duration_hours: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(2000))
    privacy_level: Mapped[PrivacyLevel] = mapped_column(
        Enum(PrivacyLevel, native_enum=False),
        default=PrivacyLevel.PRIVATE,
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(
        StringArray, default=list, nullable=False, server_default="{}"
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="work_sessions")

    __table_args__ = (Index("ix_work_sessions_project_date", "project_id", "date"),)
