"""Employer model representing who work is done on behalf of."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .types import StringArray

if TYPE_CHECKING:
    from .project import Project


class Employer(Base, TimestampMixin):
    """Represents who work is done on behalf of (current employer or self)."""

    __tablename__ = "employers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_self: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contact_info: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(String(2000))
    tags: Mapped[list[str]] = mapped_column(
        StringArray, default=list, nullable=False, server_default="{}"
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="employer",
        foreign_keys="Project.on_behalf_of_id",
    )
