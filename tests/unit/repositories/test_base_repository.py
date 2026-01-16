"""Unit tests for BaseRepository CRUD operations."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.employer import Employer
from src.mosaic.repositories.base import BaseRepository


class TestBaseRepositoryCRUD:
    """Test generic CRUD operations in BaseRepository."""

    @pytest.fixture
    async def employer_repo(self, session: AsyncSession) -> BaseRepository[Employer]:
        """Create employer repository for testing."""
        return BaseRepository(session, Employer)

    async def test_create_entity(
        self, employer_repo: BaseRepository[Employer], session: AsyncSession
    ):
        """Test creating a new entity."""
        employer = await employer_repo.create(
            name="Acme Corp",
            is_current=True,
        )

        assert employer.id is not None
        assert employer.name == "Acme Corp"
        assert employer.is_current is True
        assert employer.created_at is not None
        assert employer.updated_at is not None

    async def test_get_by_id_existing(
        self, employer_repo: BaseRepository[Employer], session: AsyncSession
    ):
        """Test retrieving existing entity by ID."""
        # Create entity
        employer = await employer_repo.create(
            name="Test Corp",
        )
        employer_id = employer.id

        # Retrieve it
        retrieved = await employer_repo.get_by_id(employer_id)

        assert retrieved is not None
        assert retrieved.id == employer_id
        assert retrieved.name == "Test Corp"

    async def test_get_by_id_nonexistent(self, employer_repo: BaseRepository[Employer]):
        """Test retrieving non-existent entity returns None."""
        result = await employer_repo.get_by_id(999999)
        assert result is None

    async def test_update_entity(
        self, employer_repo: BaseRepository[Employer], session: AsyncSession
    ):
        """Test updating an existing entity."""
        # Create entity
        employer = await employer_repo.create(
            name="Old Name",
        )
        employer_id = employer.id

        # Update it
        updated = await employer_repo.update(
            employer_id,
            name="New Name",
            is_current=True,
        )

        assert updated is not None
        assert updated.id == employer_id
        assert updated.name == "New Name"
        assert updated.is_current is True

    async def test_update_nonexistent_returns_none(self, employer_repo: BaseRepository[Employer]):
        """Test updating non-existent entity returns None."""
        result = await employer_repo.update(999999, name="New Name")
        assert result is None

    async def test_update_partial_fields(
        self, employer_repo: BaseRepository[Employer], session: AsyncSession
    ):
        """Test updating only some fields."""
        # Create entity
        employer = await employer_repo.create(
            name="Original Name",
            is_current=False,
        )
        employer_id = employer.id

        # Update only name
        updated = await employer_repo.update(employer_id, name="Updated Name")

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.is_current is False  # Should remain unchanged

    async def test_delete_existing_entity(
        self, employer_repo: BaseRepository[Employer], session: AsyncSession
    ):
        """Test deleting an existing entity."""
        # Create entity
        employer = await employer_repo.create(
            name="To Delete",
        )
        employer_id = employer.id

        # Delete it
        result = await employer_repo.delete(employer_id)
        assert result is True

        # Verify it's gone
        retrieved = await employer_repo.get_by_id(employer_id)
        assert retrieved is None

    async def test_delete_nonexistent_returns_false(self, employer_repo: BaseRepository[Employer]):
        """Test deleting non-existent entity returns False."""
        result = await employer_repo.delete(999999)
        assert result is False

    async def test_list_all_empty(self, employer_repo: BaseRepository[Employer]):
        """Test listing all entities when none exist."""
        result = await employer_repo.list_all()
        assert result == []

    async def test_list_all_multiple(
        self, employer_repo: BaseRepository[Employer], session: AsyncSession
    ):
        """Test listing all entities with multiple records."""
        # Create multiple entities
        await employer_repo.create(name="Employer 1")
        await employer_repo.create(name="Employer 2")
        await employer_repo.create(name="Employer 3")

        # List all
        result = await employer_repo.list_all()

        assert len(result) == 3
        names = [e.name for e in result]
        assert "Employer 1" in names
        assert "Employer 2" in names
        assert "Employer 3" in names

    async def test_create_with_missing_required_field_raises_error(
        self, employer_repo: BaseRepository[Employer]
    ):
        """Test creating entity without required field raises error."""
        with pytest.raises(IntegrityError):
            # Missing required 'name' field - will be None and violate NOT NULL constraint
            await employer_repo.create(is_current=True)  # type: ignore

    async def test_update_ignores_invalid_fields(
        self, employer_repo: BaseRepository[Employer], session: AsyncSession
    ):
        """Test updating with invalid field names doesn't cause errors."""
        # Create entity
        employer = await employer_repo.create(
            name="Test",
        )
        employer_id = employer.id

        # Update with invalid field (should be ignored)
        updated = await employer_repo.update(
            employer_id,
            name="Updated",
            invalid_field="should be ignored",  # type: ignore
        )

        assert updated is not None
        assert updated.name == "Updated"
        assert not hasattr(updated, "invalid_field")
