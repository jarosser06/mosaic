"""Person model with employment history tracking."""

from datetime import date
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .types import StringArray

if TYPE_CHECKING:
    from .client import Client
    from .meeting import MeetingAttendee


class EmploymentHistory(Base):
    """Temporal tracking of person-client relationships."""

    __tablename__ = "employment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[Optional[str]] = mapped_column(String(255))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationships
    person: Mapped["Person"] = relationship("Person", back_populates="employments")
    client: Mapped["Client"] = relationship("Client", back_populates="employments")


class Person(Base, TimestampMixin):
    """Individuals with rich profiles that persist across job changes."""

    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_stakeholder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(200))
    title: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(StringArray, default=list, nullable=False)
    additional_info: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # Relationships
    employments: Mapped[list["EmploymentHistory"]] = relationship(
        "EmploymentHistory",
        back_populates="person",
        cascade="all, delete-orphan",
    )
    meeting_attendances: Mapped[list["MeetingAttendee"]] = relationship(
        "MeetingAttendee", back_populates="person"
    )
