"""Schemas for bookmark operations."""

from datetime import datetime

from pydantic import Field

from mosaic.schemas.common import (
    BaseSchema,
    EntityType,
    PrivacyLevel,
    TimezoneAwareDatetimeMixin,
)


class AddBookmarkInput(BaseSchema):
    """Input schema for adding a new bookmark."""

    title: str = Field(
        description="Bookmark title",
        min_length=1,
        max_length=500,
        examples=[
            "Python AsyncIO Documentation",
            "React Hooks Guide",
            "PostgreSQL Performance Tips",
        ],
    )

    url: str = Field(
        description="Bookmark URL",
        min_length=1,
        max_length=2000,
        examples=[
            "https://docs.python.org/3/library/asyncio.html",
            "https://react.dev/reference/react/hooks",
        ],
    )

    description: str | None = Field(
        default=None,
        description="Detailed description of the bookmark",
        max_length=2000,
        examples=["Comprehensive guide to async programming in Python"],
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of entity this bookmark is attached to",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of the entity this bookmark is attached to",
        gt=0,
        examples=[1, 42],
    )

    privacy_level: PrivacyLevel = Field(
        default=PrivacyLevel.PRIVATE,
        description="Privacy level for this bookmark",
        examples=["private", "internal", "public"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["python", "async"], ["documentation", "react"]],
    )


class AddBookmarkOutput(BaseSchema, TimezoneAwareDatetimeMixin):
    """Output schema for added bookmark."""

    id: int = Field(
        description="Unique identifier for the bookmark",
        examples=[1, 42],
    )

    title: str = Field(
        description="Bookmark title",
        examples=["Python AsyncIO Documentation"],
    )

    url: str = Field(
        description="Bookmark URL",
        examples=["https://docs.python.org/3/library/asyncio.html"],
    )

    description: str | None = Field(
        default=None,
        description="Detailed description",
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Type of attached entity",
    )

    entity_id: int | None = Field(
        default=None,
        description="ID of attached entity",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level",
        examples=["private"],
    )

    tags: list[str] = Field(
        description="Tags for categorization",
        examples=[["python", "async"], []],
    )

    created_at: datetime = Field(
        description="Timestamp when bookmark was created",
        examples=["2026-01-15T10:00:00-05:00"],
    )

    updated_at: datetime = Field(
        description="Timestamp when bookmark was last updated",
        examples=["2026-01-15T10:00:00-05:00"],
    )


class UpdateBookmarkInput(BaseSchema):
    """Input schema for updating a bookmark."""

    bookmark_id: int = Field(
        description="ID of the bookmark to update",
        gt=0,
        examples=[1, 42],
    )

    title: str | None = Field(
        default=None,
        description="Updated title",
        min_length=1,
        max_length=500,
    )

    url: str | None = Field(
        default=None,
        description="Updated URL",
        min_length=1,
        max_length=2000,
    )

    description: str | None = Field(
        default=None,
        description="Updated description",
        max_length=2000,
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Updated entity type",
    )

    entity_id: int | None = Field(
        default=None,
        description="Updated entity ID",
        gt=0,
    )

    privacy_level: PrivacyLevel | None = Field(
        default=None,
        description="Updated privacy level",
    )

    tags: list[str] | None = Field(
        default=None,
        description="Updated tags",
    )


class UpdateBookmarkOutput(AddBookmarkOutput):
    """Output schema for updated bookmark."""

    pass


class ListBookmarksInput(BaseSchema):
    """Input schema for listing/filtering bookmarks."""

    entity_type: EntityType | None = Field(
        default=None,
        description="Filter by entity type the bookmark is attached to",
        examples=["person", "client", "project", "meeting"],
    )

    entity_id: int | None = Field(
        default=None,
        description="Filter by specific entity ID",
        gt=0,
        examples=[1, 42],
    )

    search_query: str | None = Field(
        default=None,
        description="Search in title or URL (case-insensitive)",
        examples=["python", "react", "docs.python.org"],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Filter by tags (returns bookmarks with ANY of these tags)",
        examples=[["python"], ["documentation", "tutorial"]],
    )


class BookmarkItem(BaseSchema, TimezoneAwareDatetimeMixin):
    """Individual bookmark in list results."""

    id: int = Field(
        description="Unique identifier",
        examples=[1, 42],
    )

    title: str = Field(
        description="Bookmark title",
        examples=["Python AsyncIO Documentation"],
    )

    url: str = Field(
        description="Bookmark URL",
        examples=["https://docs.python.org/3/library/asyncio.html"],
    )

    description: str | None = Field(
        default=None,
        description="Detailed description",
    )

    entity_type: EntityType | None = Field(
        default=None,
        description="Attached entity type",
    )

    entity_id: int | None = Field(
        default=None,
        description="Attached entity ID",
    )

    privacy_level: PrivacyLevel = Field(
        description="Privacy level",
    )

    tags: list[str] = Field(
        description="Tags",
        examples=[["python"], []],
    )

    created_at: datetime = Field(
        description="When created",
    )

    updated_at: datetime = Field(
        description="When last updated",
    )


class ListBookmarksOutput(BaseSchema):
    """Output schema for bookmark list."""

    bookmarks: list[BookmarkItem] = Field(
        description="List of bookmarks matching the filters",
        examples=[[]],
    )

    total_count: int = Field(
        description="Total number of bookmarks returned",
        examples=[0, 5, 42],
    )


class DeleteBookmarkInput(BaseSchema):
    """Input schema for deleting a bookmark."""

    bookmark_id: int = Field(
        description="ID of the bookmark to delete",
        gt=0,
        examples=[1, 42],
    )


class DeleteBookmarkOutput(BaseSchema):
    """Output schema for deleted bookmark confirmation."""

    success: bool = Field(
        description="Whether the deletion was successful",
        examples=[True],
    )

    message: str = Field(
        description="Confirmation message",
        examples=["Bookmark deleted successfully"],
    )
