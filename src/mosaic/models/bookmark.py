"""Bookmark model for resource link management."""

from typing import Optional

from sqlalchemy import Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, EntityType, PrivacyLevel, TimestampMixin
from .types import StringArray


class Bookmark(Base, TimestampMixin):
    """Resource links with optional entity associations and tag-based organization."""

    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000))
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

    __table_args__ = (Index("ix_bookmarks_entity", "entity_type", "entity_id"),)
