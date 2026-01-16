"""Note model for timestamped annotations on any entity."""

from typing import Optional

from sqlalchemy import Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, EntityType, PrivacyLevel, TimestampMixin
from .types import StringArray


class Note(Base, TimestampMixin):
    """Timestamped notes attachable to any entity type."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(5000), nullable=False)
    privacy_level: Mapped[PrivacyLevel] = mapped_column(
        Enum(PrivacyLevel, native_enum=False),
        default=PrivacyLevel.PRIVATE,
        nullable=False,
    )
    entity_type: Mapped[Optional[EntityType]] = mapped_column(Enum(EntityType, native_enum=False))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(
        StringArray, default=list, nullable=False, server_default="{}"
    )

    __table_args__ = (Index("ix_notes_entity", "entity_type", "entity_id"),)
