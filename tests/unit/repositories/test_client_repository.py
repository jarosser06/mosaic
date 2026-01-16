"""Unit tests for ClientRepository custom queries."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.repositories.client_repository import ClientRepository


class TestClientRepositoryQueries:
    """Test ClientRepository custom query methods."""

    @pytest.fixture
    async def repo(self, session: AsyncSession) -> ClientRepository:
        """Create client repository."""
        return ClientRepository(session)

    async def test_get_by_name_existing(self, repo: ClientRepository, session: AsyncSession):
        """Test finding client by name."""
        # Create clients
        client1 = Client(
            name="Acme Corp",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        client2 = Client(
            name="John Doe",
            type=ClientType.INDIVIDUAL,
            status=ClientStatus.ACTIVE,
        )
        session.add_all([client1, client2])
        await session.flush()

        # Find by name
        result = await repo.get_by_name("John Doe")

        assert result is not None
        assert result.name == "John Doe"
        assert result.type == ClientType.INDIVIDUAL

    async def test_get_by_name_nonexistent(self, repo: ClientRepository):
        """Test finding client by name returns None when not found."""
        result = await repo.get_by_name("Nonexistent Client")
        assert result is None

    async def test_list_active_clients_only(self, repo: ClientRepository, session: AsyncSession):
        """Test listing only active clients."""
        # Create mixed status clients
        active1 = Client(
            name="Active Corp",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        active2 = Client(
            name="Active Individual",
            type=ClientType.INDIVIDUAL,
            status=ClientStatus.ACTIVE,
        )
        past = Client(
            name="Past Client",
            type=ClientType.COMPANY,
            status=ClientStatus.PAST,
        )
        session.add_all([active1, active2, past])
        await session.flush()

        # List active only
        result = await repo.list_active()

        assert len(result) == 2
        names = {c.name for c in result}
        assert "Active Corp" in names
        assert "Active Individual" in names
        assert "Past Client" not in names

    async def test_list_active_empty(self, repo: ClientRepository):
        """Test listing active clients when none exist."""
        result = await repo.list_active()
        assert result == []

    async def test_create_company_client(self, repo: ClientRepository, session: AsyncSession):
        """Test creating a company client."""
        client = await repo.create(
            name="Tech Industries",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            notes="Technology consulting company",
        )

        assert client.id is not None
        assert client.name == "Tech Industries"
        assert client.type == ClientType.COMPANY
        assert client.status == ClientStatus.ACTIVE
        assert client.notes == "Technology consulting company"

    async def test_create_individual_client(self, repo: ClientRepository, session: AsyncSession):
        """Test creating an individual client."""
        client = await repo.create(
            name="Jane Smith",
            type=ClientType.INDIVIDUAL,
            status=ClientStatus.ACTIVE,
        )

        assert client.id is not None
        assert client.name == "Jane Smith"
        assert client.type == ClientType.INDIVIDUAL

    async def test_update_client_status_to_past(
        self, repo: ClientRepository, session: AsyncSession
    ):
        """Test updating client status from active to past."""
        # Create active client
        client = await repo.create(
            name="Test Client",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        client_id = client.id

        # Update to past
        updated = await repo.update(client_id, status=ClientStatus.PAST)

        assert updated is not None
        assert updated.status == ClientStatus.PAST

        # Verify not in active list
        active_clients = await repo.list_active()
        assert len(active_clients) == 0

    async def test_list_all_includes_all_statuses(
        self, repo: ClientRepository, session: AsyncSession
    ):
        """Test list_all includes both active and past clients."""
        # Create clients with different statuses
        await repo.create(
            name="Active Client",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        await repo.create(
            name="Past Client",
            type=ClientType.COMPANY,
            status=ClientStatus.PAST,
        )

        # List all
        all_clients = await repo.list_all()

        assert len(all_clients) == 2

    async def test_get_by_name_case_sensitive(self, repo: ClientRepository, session: AsyncSession):
        """Test client name lookup is case-sensitive."""
        # Create client
        client = Client(
            name="Tech Corp",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        session.add(client)
        await session.flush()

        # Exact match works
        result = await repo.get_by_name("Tech Corp")
        assert result is not None

        # Different case does not match
        result = await repo.get_by_name("TECH CORP")
        assert result is None
