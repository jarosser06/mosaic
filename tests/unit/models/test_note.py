"""Tests for Note model."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType, PrivacyLevel
from src.mosaic.models.note import Note


@pytest.mark.asyncio
async def test_note_creation_minimal(session: AsyncSession) -> None:
    """Test creating note with minimal required fields."""
    note = Note(
        text="This is a test note",
        entity_type=EntityType.PROJECT,
        entity_id=42,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)

    assert note.id is not None
    assert note.text == "This is a test note"
    assert note.entity_type == EntityType.PROJECT
    assert note.entity_id == 42
    assert note.privacy_level == PrivacyLevel.PRIVATE
    assert note.created_at is not None
    assert note.updated_at is not None


@pytest.mark.asyncio
async def test_note_creation_full(session: AsyncSession) -> None:
    """Test creating note with all fields populated."""
    note = Note(
        text="Meeting notes from client discussion",
        privacy_level=PrivacyLevel.INTERNAL,
        entity_type=EntityType.MEETING,
        entity_id=123,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)

    assert note.text == "Meeting notes from client discussion"
    assert note.privacy_level == PrivacyLevel.INTERNAL
    assert note.entity_type == EntityType.MEETING
    assert note.entity_id == 123


@pytest.mark.parametrize(
    "privacy_level",
    [PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL, PrivacyLevel.PRIVATE],
)
@pytest.mark.asyncio
async def test_note_privacy_levels(session: AsyncSession, privacy_level: PrivacyLevel) -> None:
    """Test all privacy level values for notes."""
    note = Note(
        text="Test note",
        entity_type=EntityType.PROJECT,
        entity_id=1,
        privacy_level=privacy_level,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)

    assert note.privacy_level == privacy_level


@pytest.mark.parametrize(
    "entity_type,entity_id",
    [
        (EntityType.PERSON, 1),
        (EntityType.CLIENT, 2),
        (EntityType.PROJECT, 3),
        (EntityType.EMPLOYER, 4),
        (EntityType.WORK_SESSION, 5),
        (EntityType.MEETING, 6),
        (EntityType.REMINDER, 7),
    ],
)
@pytest.mark.asyncio
async def test_note_entity_links(
    session: AsyncSession, entity_type: EntityType, entity_id: int
) -> None:
    """Test notes attached to different entity types."""
    note = Note(
        text=f"Note for {entity_type.value}",
        entity_type=entity_type,
        entity_id=entity_id,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)

    assert note.entity_type == entity_type
    assert note.entity_id == entity_id


@pytest.mark.asyncio
async def test_note_entity_composite_index(session: AsyncSession) -> None:
    """Test composite index on entity_type and entity_id."""
    note1 = Note(text="Note 1", entity_type=EntityType.PROJECT, entity_id=1)
    note2 = Note(text="Note 2", entity_type=EntityType.PROJECT, entity_id=1)
    note3 = Note(text="Note 3", entity_type=EntityType.PROJECT, entity_id=2)
    note4 = Note(text="Note 4", entity_type=EntityType.PERSON, entity_id=1)
    session.add_all([note1, note2, note3, note4])
    await session.flush()

    # Query by entity_type and entity_id
    stmt = select(Note).where(Note.entity_type == EntityType.PROJECT, Note.entity_id == 1)
    result = await session.execute(stmt)
    notes = result.scalars().all()

    assert len(notes) == 2
    assert all(n.entity_type == EntityType.PROJECT for n in notes)
    assert all(n.entity_id == 1 for n in notes)


@pytest.mark.asyncio
async def test_note_long_text(session: AsyncSession) -> None:
    """Test note with long text field."""
    long_text = "x" * 5000

    note = Note(
        text=long_text,
        entity_type=EntityType.PROJECT,
        entity_id=1,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)

    assert len(note.text) == 5000


@pytest.mark.asyncio
async def test_note_update_text(session: AsyncSession) -> None:
    """Test updating note text."""
    note = Note(
        text="Original text",
        entity_type=EntityType.PROJECT,
        entity_id=1,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)

    original_updated = note.updated_at

    note.text = "Updated text"
    await session.flush()
    await session.refresh(note)

    assert note.text == "Updated text"
    assert note.updated_at >= original_updated


@pytest.mark.asyncio
async def test_note_query_by_entity(session: AsyncSession) -> None:
    """Test querying notes by entity."""
    # Create notes for different entities
    note1 = Note(text="Project note 1", entity_type=EntityType.PROJECT, entity_id=10)
    note2 = Note(text="Project note 2", entity_type=EntityType.PROJECT, entity_id=10)
    note3 = Note(text="Person note", entity_type=EntityType.PERSON, entity_id=20)
    session.add_all([note1, note2, note3])
    await session.flush()

    # Query all notes for project 10
    stmt = select(Note).where(Note.entity_type == EntityType.PROJECT, Note.entity_id == 10)
    result = await session.execute(stmt)
    project_notes = result.scalars().all()

    assert len(project_notes) == 2
    assert all("Project note" in n.text for n in project_notes)
