"""Unit tests for EmployerRepository custom queries."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.employer import Employer
from src.mosaic.repositories.employer_repository import EmployerRepository


class TestEmployerRepositoryQueries:
    """Test EmployerRepository custom query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> EmployerRepository:
        """Create employer repository."""
        return EmployerRepository(session)

    async def test_get_current_employer(self, repo: EmployerRepository, session: AsyncSession):
        """Test getting current employer."""
        # Create multiple employers
        emp1 = Employer(name="Old Corp", is_current=False)
        emp2 = Employer(name="Current Corp", is_current=True)
        emp3 = Employer(name="Another Old", is_current=False)
        session.add_all([emp1, emp2, emp3])
        await session.flush()

        # Get current employer
        result = await repo.get_current_employer()

        assert result is not None
        assert result.name == "Current Corp"
        assert result.is_current is True

    async def test_get_current_employer_none_exists(self, repo: EmployerRepository):
        """Test getting current employer when none marked as current."""
        result = await repo.get_current_employer()
        assert result is None

    async def test_get_self_employer(self, repo: EmployerRepository, session: AsyncSession):
        """Test getting self employer."""
        # Create multiple employers
        emp1 = Employer(name="Company A", is_self=False)
        emp2 = Employer(name="Self Employed", is_self=True)
        emp3 = Employer(name="Company B", is_self=False)
        session.add_all([emp1, emp2, emp3])
        await session.flush()

        # Get self employer
        result = await repo.get_self_employer()

        assert result is not None
        assert result.name == "Self Employed"
        assert result.is_self is True

    async def test_get_self_employer_none_exists(self, repo: EmployerRepository):
        """Test getting self employer when none marked as self."""
        result = await repo.get_self_employer()
        assert result is None

    async def test_get_by_name_existing(self, repo: EmployerRepository, session: AsyncSession):
        """Test finding employer by name."""
        # Create employers
        emp1 = Employer(name="Acme Corp")
        emp2 = Employer(name="Tech Industries")
        session.add_all([emp1, emp2])
        await session.flush()

        # Find by name
        result = await repo.get_by_name("Tech Industries")

        assert result is not None
        assert result.name == "Tech Industries"

    async def test_get_by_name_nonexistent(self, repo: EmployerRepository):
        """Test finding employer by name returns None when not found."""
        result = await repo.get_by_name("Nonexistent Corp")
        assert result is None

    async def test_get_by_name_case_sensitive(
        self, repo: EmployerRepository, session: AsyncSession
    ):
        """Test employer name lookup is case-sensitive."""
        # Create employer
        emp = Employer(name="Tech Corp")
        session.add(emp)
        await session.flush()

        # Exact match works
        result = await repo.get_by_name("Tech Corp")
        assert result is not None

        # Different case does not match
        result = await repo.get_by_name("TECH CORP")
        assert result is None

    async def test_multiple_employers_single_current(
        self, repo: EmployerRepository, session: AsyncSession
    ):
        """Test having multiple employers with only one current."""
        # Create multiple employers
        await repo.create(name="Past Employer 1", is_current=False)
        await repo.create(name="Current Employer", is_current=True)
        await repo.create(name="Past Employer 2", is_current=False)

        # Get current
        current = await repo.get_current_employer()

        assert current is not None
        assert current.name == "Current Employer"

        # List all should return 3
        all_employers = await repo.list_all()
        assert len(all_employers) == 3
