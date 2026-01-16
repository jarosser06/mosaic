"""Unit tests for PersonRepository including employment history."""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.person import Person
from src.mosaic.repositories.person_repository import PersonRepository


class TestPersonRepositoryBasicQueries:
    """Test basic PersonRepository query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> PersonRepository:
        """Create person repository."""
        return PersonRepository(session)

    async def test_get_by_email_existing(self, repo: PersonRepository, session: AsyncSession):
        """Test finding person by email."""
        # Create person
        person = Person(
            full_name="John Doe",
            email="john@example.com",
            phone="+1-555-0123",
        )
        session.add(person)
        await session.flush()

        # Find by email
        result = await repo.get_by_email("john@example.com")

        assert result is not None
        assert result.email == "john@example.com"
        assert result.full_name == "John Doe"

    async def test_get_by_email_nonexistent(self, repo: PersonRepository):
        """Test finding person by email returns None when not found."""
        result = await repo.get_by_email("nonexistent@example.com")
        assert result is None

    async def test_search_by_name_partial_match(
        self, repo: PersonRepository, session: AsyncSession
    ):
        """Test searching people by partial name."""
        # Create multiple people
        person1 = Person(full_name="John Smith")
        person2 = Person(full_name="Jane Smith")
        person3 = Person(full_name="Bob Johnson")
        session.add_all([person1, person2, person3])
        await session.flush()

        # Search for "Smith"
        results = await repo.search_by_name("Smith")

        assert len(results) == 2
        names = {p.full_name for p in results}
        assert "John Smith" in names
        assert "Jane Smith" in names
        assert "Bob Johnson" not in names

    async def test_search_by_name_case_insensitive(
        self, repo: PersonRepository, session: AsyncSession
    ):
        """Test name search is case-insensitive."""
        # Create person
        person = Person(full_name="Alice Johnson")
        session.add(person)
        await session.flush()

        # Search with different cases
        results_lower = await repo.search_by_name("alice")
        results_upper = await repo.search_by_name("ALICE")
        results_mixed = await repo.search_by_name("AlIcE")

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1

    async def test_list_stakeholders(self, repo: PersonRepository, session: AsyncSession):
        """Test listing people marked as stakeholders."""
        # Create mixed people
        stakeholder1 = Person(full_name="Alice", is_stakeholder=True)
        stakeholder2 = Person(full_name="Bob", is_stakeholder=True)
        non_stakeholder = Person(full_name="Charlie", is_stakeholder=False)
        session.add_all([stakeholder1, stakeholder2, non_stakeholder])
        await session.flush()

        # List stakeholders
        results = await repo.list_stakeholders()

        assert len(results) == 2
        names = {p.full_name for p in results}
        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" not in names

    async def test_list_stakeholders_empty(self, repo: PersonRepository):
        """Test listing stakeholders when none exist."""
        result = await repo.list_stakeholders()
        assert result == []


class TestPersonRepositoryEmploymentHistory:
    """Test employment history management methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> PersonRepository:
        """Create person repository."""
        return PersonRepository(session)

    @pytest.fixture
    async def test_person(self, session: AsyncSession) -> Person:
        """Create test person."""
        person = Person(full_name="Test Person", email="test@example.com")
        session.add(person)
        await session.flush()
        await session.refresh(person)
        return person

    @pytest.fixture
    async def test_client(self, session: AsyncSession) -> Client:
        """Create test client."""
        client = Client(
            name="Test Client",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        session.add(client)
        await session.flush()
        await session.refresh(client)
        return client

    async def test_add_employment(
        self,
        repo: PersonRepository,
        session: AsyncSession,
        test_person: Person,
        test_client: Client,
    ):
        """Test adding employment history record."""
        employment = await repo.add_employment(
            person_id=test_person.id,
            client_id=test_client.id,
            start_date=date(2024, 1, 1),
            role="Software Engineer",
        )

        assert employment.id is not None
        assert employment.person_id == test_person.id
        assert employment.client_id == test_client.id
        assert employment.start_date == date(2024, 1, 1)
        assert employment.role == "Software Engineer"
        assert employment.end_date is None

    async def test_add_employment_with_end_date(
        self,
        repo: PersonRepository,
        session: AsyncSession,
        test_person: Person,
        test_client: Client,
    ):
        """Test adding completed employment record."""
        employment = await repo.add_employment(
            person_id=test_person.id,
            client_id=test_client.id,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            role="Contractor",
        )

        assert employment.end_date == date(2023, 12, 31)

    async def test_get_by_id_with_employments(
        self,
        repo: PersonRepository,
        session: AsyncSession,
        test_person: Person,
        test_client: Client,
    ):
        """Test eager loading employment history."""
        # Add employment
        await repo.add_employment(
            person_id=test_person.id,
            client_id=test_client.id,
            start_date=date(2024, 1, 1),
        )

        # Get person with employments
        result = await repo.get_by_id_with_employments(test_person.id)

        assert result is not None
        assert result.id == test_person.id
        assert len(result.employments) == 1
        assert result.employments[0].client_id == test_client.id

    async def test_get_current_employers(
        self,
        repo: PersonRepository,
        session: AsyncSession,
        test_person: Person,
        test_client: Client,
    ):
        """Test getting current employment records."""
        # Add current employment (no end_date)
        await repo.add_employment(
            person_id=test_person.id,
            client_id=test_client.id,
            start_date=date(2024, 1, 1),
        )

        # Add past employment (with end_date)
        client2 = Client(name="Past Client", type=ClientType.COMPANY, status=ClientStatus.PAST)
        session.add(client2)
        await session.flush()

        await repo.add_employment(
            person_id=test_person.id,
            client_id=client2.id,
            start_date=date(2022, 1, 1),
            end_date=date(2023, 12, 31),
        )

        # Get current employers
        current = await repo.get_current_employers(test_person.id)

        assert len(current) == 1
        assert current[0].client_id == test_client.id
        assert current[0].end_date is None

    async def test_get_employments_at_date(
        self,
        repo: PersonRepository,
        session: AsyncSession,
        test_person: Person,
        test_client: Client,
    ):
        """Test getting employment active at specific date."""
        # Add employment: Jan 1 2024 - Dec 31 2024
        await repo.add_employment(
            person_id=test_person.id,
            client_id=test_client.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        # Check date within range
        results = await repo.get_employments_at_date(test_person.id, date(2024, 6, 15))
        assert len(results) == 1

        # Check date before range
        results = await repo.get_employments_at_date(test_person.id, date(2023, 12, 31))
        assert len(results) == 0

        # Check date after range
        results = await repo.get_employments_at_date(test_person.id, date(2025, 1, 1))
        assert len(results) == 0

    async def test_get_employments_at_date_ongoing(
        self,
        repo: PersonRepository,
        session: AsyncSession,
        test_person: Person,
        test_client: Client,
    ):
        """Test getting ongoing employment (no end_date)."""
        # Add ongoing employment
        await repo.add_employment(
            person_id=test_person.id,
            client_id=test_client.id,
            start_date=date(2024, 1, 1),
            # No end_date
        )

        # Should be active at any date after start
        results = await repo.get_employments_at_date(test_person.id, date(2025, 12, 31))
        assert len(results) == 1

    async def test_get_employments_in_date_range(
        self,
        repo: PersonRepository,
        session: AsyncSession,
        test_person: Person,
        test_client: Client,
    ):
        """Test getting employments that overlap with date range."""
        # Add employment: Jan 1 2024 - Dec 31 2024
        await repo.add_employment(
            person_id=test_person.id,
            client_id=test_client.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        # Range completely overlapping
        results = await repo.get_employments_in_date_range(
            test_person.id, date(2024, 3, 1), date(2024, 9, 30)
        )
        assert len(results) == 1

        # Range partially overlapping (start)
        results = await repo.get_employments_in_date_range(
            test_person.id, date(2023, 6, 1), date(2024, 6, 30)
        )
        assert len(results) == 1

        # Range partially overlapping (end)
        results = await repo.get_employments_in_date_range(
            test_person.id, date(2024, 6, 1), date(2025, 6, 30)
        )
        assert len(results) == 1

        # Range completely outside
        results = await repo.get_employments_in_date_range(
            test_person.id, date(2023, 1, 1), date(2023, 12, 31)
        )
        assert len(results) == 0

    async def test_get_employments_in_date_range_invalid_range(
        self, repo: PersonRepository, test_person: Person
    ):
        """Test date range validation."""
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            await repo.get_employments_in_date_range(
                test_person.id, date(2024, 12, 31), date(2024, 1, 1)
            )
