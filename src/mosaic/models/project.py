"""Project model representing work initiatives."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, ProjectStatus, TimestampMixin
from .types import StringArray

if TYPE_CHECKING:
    from .client import Client
    from .employer import Employer
    from .meeting import Meeting
    from .work_session import WorkSession


class Project(Base, TimestampMixin):
    """Work initiatives done on behalf of an employer for a client."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    on_behalf_of_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("employers.id", ondelete="RESTRICT")
    )
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(2000))
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    tags: Mapped[list[str]] = mapped_column(
        StringArray, default=list, nullable=False, server_default="{}"
    )

    # Relationships
    employer: Mapped[Optional["Employer"]] = relationship(
        "Employer",
        back_populates="projects",
        foreign_keys=[on_behalf_of_id],
    )
    client: Mapped["Client"] = relationship("Client", back_populates="projects")
    work_sessions: Mapped[list["WorkSession"]] = relationship(
        "WorkSession", back_populates="project"
    )
    meetings: Mapped[list["Meeting"]] = relationship("Meeting", back_populates="project")
