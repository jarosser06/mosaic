"""Meeting model with attendees and optional project association."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PrivacyLevel, TimestampMixin
from .types import StringArray

if TYPE_CHECKING:
    from .person import Person
    from .project import Project


class MeetingAttendee(Base):
    """Association table for meeting-person many-to-many relationship."""

    __tablename__ = "meeting_attendees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="attendees")
    person: Mapped["Person"] = relationship("Person", back_populates="meeting_attendances")


class Meeting(Base, TimestampMixin):
    """Discussion events with people, optionally tied to projects."""

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(2000))
    privacy_level: Mapped[PrivacyLevel] = mapped_column(
        Enum(PrivacyLevel, native_enum=False),
        default=PrivacyLevel.PRIVATE,
        nullable=False,
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL")
    )
    meeting_type: Mapped[Optional[str]] = mapped_column(String(100))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    tags: Mapped[list[str]] = mapped_column(
        StringArray, default=list, nullable=False, server_default="{}"
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="meetings")
    attendees: Mapped[list["MeetingAttendee"]] = relationship(
        "MeetingAttendee",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
