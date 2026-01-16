"""Client model representing companies or individuals work is done for."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, ClientStatus, ClientType, TimestampMixin
from .types import StringArray

if TYPE_CHECKING:
    from .person import EmploymentHistory, Person
    from .project import Project


class Client(Base, TimestampMixin):
    """Companies or individuals that work is done for."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[ClientType] = mapped_column(Enum(ClientType, native_enum=False), nullable=False)
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus, native_enum=False),
        default=ClientStatus.ACTIVE,
        nullable=False,
    )
    contact_person_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("people.id", ondelete="SET NULL")
    )
    notes: Mapped[Optional[str]] = mapped_column(String(2000))
    tags: Mapped[list[str]] = mapped_column(StringArray, default=list, nullable=False)

    # Relationships
    contact_person: Mapped[Optional["Person"]] = relationship("Person")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="client")
    employments: Mapped[list["EmploymentHistory"]] = relationship(
        "EmploymentHistory", back_populates="client"
    )
