"""User profile model with preferences and settings."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, WeekBoundary


class User(Base, TimestampMixin):
    """User profile with timezone, week boundaries, and working preferences."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    week_boundary: Mapped[WeekBoundary] = mapped_column(
        Enum(WeekBoundary, native_enum=False),
        default=WeekBoundary.MONDAY_FRIDAY,
        nullable=False,
    )
    working_hours_start: Mapped[Optional[int]] = mapped_column(Integer)
    working_hours_end: Mapped[Optional[int]] = mapped_column(Integer)
    communication_style: Mapped[Optional[str]] = mapped_column(String(1000))
    work_approach: Mapped[Optional[str]] = mapped_column(String(1000))
    profile_last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
