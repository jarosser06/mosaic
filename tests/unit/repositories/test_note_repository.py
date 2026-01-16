"""Unit tests for NoteRepository entity-based queries."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType, PrivacyLevel
from src.mosaic.models.note import Note
from src.mosaic.models.project import Project
from src.mosaic.repositories.note_repository import NoteRepository


class TestNoteRepositoryQueries:
    """Test NoteRepository custom query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> NoteRepository:
        """Create note repository."""
        return NoteRepository(session)

    async def test_list_by_entity(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test listing notes for a specific entity."""
        # Create notes for project
        note1 = Note(
            text="First note about the project",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )
        note2 = Note(
            text="Second note about the project",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )
        # Create note for different entity
        note3 = Note(
            text="Note about different entity",
            entity_type=EntityType.MEETING,
            entity_id=999,
        )
        session.add_all([note1, note2, note3])
        await session.flush()

        # List notes for project
        results = await repo.list_by_entity(EntityType.PROJECT, project.id)

        assert len(results) == 2
        texts = {n.text for n in results}
        assert "First note about the project" in texts
        assert "Second note about the project" in texts
        assert "Note about different entity" not in texts

    async def test_list_by_entity_empty(self, repo: NoteRepository, project: Project):
        """Test listing notes for entity with no notes."""
        results = await repo.list_by_entity(EntityType.PROJECT, project.id)
        assert results == []

    async def test_list_by_entity_ordered_by_created_at(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test notes are ordered by creation time (descending)."""
        # Create notes in sequence
        note1 = Note(
            text="First note",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )
        session.add(note1)
        await session.flush()

        note2 = Note(
            text="Second note",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )
        session.add(note2)
        await session.flush()

        note3 = Note(
            text="Third note",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )
        session.add(note3)
        await session.flush()

        # List notes
        results = await repo.list_by_entity(EntityType.PROJECT, project.id)

        # Should be in reverse chronological order (newest first)
        assert len(results) == 3
        assert results[0].text == "Third note"
        assert results[1].text == "Second note"
        assert results[2].text == "First note"

    async def test_create_note_with_privacy(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test creating note with privacy level."""
        note = await repo.create(
            text="Private project note",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            privacy_level=PrivacyLevel.PRIVATE,
        )

        assert note.id is not None
        assert note.text == "Private project note"
        assert note.privacy_level == PrivacyLevel.PRIVATE

    async def test_create_note_default_privacy(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test default privacy level is PRIVATE."""
        note = await repo.create(
            text="Note with default privacy",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )

        assert note.privacy_level == PrivacyLevel.PRIVATE

    async def test_update_note_content(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test updating note content."""
        # Create note
        note = await repo.create(
            text="Original content",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )

        # Update content
        updated = await repo.update(note.id, text="Updated content")

        assert updated is not None
        assert updated.text == "Updated content"

    async def test_update_note_privacy_level(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test updating note privacy level."""
        # Create private note
        note = await repo.create(
            text="Test note",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            privacy_level=PrivacyLevel.PRIVATE,
        )

        # Update to public
        updated = await repo.update(note.id, privacy_level=PrivacyLevel.PUBLIC)

        assert updated is not None
        assert updated.privacy_level == PrivacyLevel.PUBLIC

    async def test_delete_note(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test deleting a note."""
        # Create note
        note = await repo.create(
            text="Note to delete",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )

        # Delete it
        result = await repo.delete(note.id)
        assert result is True

        # Verify removed
        notes = await repo.list_by_entity(EntityType.PROJECT, project.id)
        assert len(notes) == 0

    async def test_notes_for_different_entity_types(
        self, repo: NoteRepository, session: AsyncSession
    ):
        """Test notes can be attached to different entity types."""
        # Create notes for different entity types
        await repo.create(
            text="Project note",
            entity_type=EntityType.PROJECT,
            entity_id=1,
        )
        await repo.create(
            text="Meeting note",
            entity_type=EntityType.MEETING,
            entity_id=2,
        )
        await repo.create(
            text="Person note",
            entity_type=EntityType.PERSON,
            entity_id=3,
        )

        # Verify each can be retrieved separately
        project_notes = await repo.list_by_entity(EntityType.PROJECT, 1)
        meeting_notes = await repo.list_by_entity(EntityType.MEETING, 2)
        person_notes = await repo.list_by_entity(EntityType.PERSON, 3)

        assert len(project_notes) == 1
        assert len(meeting_notes) == 1
        assert len(person_notes) == 1

    async def test_multiple_notes_same_entity(
        self,
        repo: NoteRepository,
        session: AsyncSession,
        project: Project,
    ):
        """Test multiple notes can be attached to same entity."""
        # Create 5 notes for same project
        for i in range(5):
            await repo.create(
                text=f"Note {i+1}",
                entity_type=EntityType.PROJECT,
                entity_id=project.id,
            )

        # List all notes
        notes = await repo.list_by_entity(EntityType.PROJECT, project.id)

        assert len(notes) == 5
