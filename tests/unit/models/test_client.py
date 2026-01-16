"""Tests for Client model."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.mosaic.models.base import ClientStatus, ClientType
from src.mosaic.models.client import Client
from src.mosaic.models.employer import Employer
from src.mosaic.models.project import Project, ProjectStatus


@pytest.mark.asyncio
async def test_client_creation_minimal(session: AsyncSession) -> None:
    """Test creating client with minimal required fields."""
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add(client)
    await session.flush()
    await session.refresh(client)

    assert client.id is not None
    assert client.name == "Test Client"
    assert client.type == ClientType.COMPANY
    assert client.status == ClientStatus.ACTIVE
    assert client.contact_person_id is None
    assert client.notes is None
    assert client.created_at is not None
    assert client.updated_at is not None


@pytest.mark.asyncio
async def test_client_creation_full(session: AsyncSession) -> None:
    """Test creating client with all fields populated."""
    client = Client(
        name="Acme Inc",
        type=ClientType.COMPANY,
        status=ClientStatus.ACTIVE,
        notes="Major client, handles billing monthly",
    )
    session.add(client)
    await session.flush()
    await session.refresh(client)

    assert client.name == "Acme Inc"
    assert client.type == ClientType.COMPANY
    assert client.status == ClientStatus.ACTIVE
    assert client.notes == "Major client, handles billing monthly"


@pytest.mark.parametrize(
    "client_type",
    [ClientType.COMPANY, ClientType.INDIVIDUAL],
)
@pytest.mark.asyncio
async def test_client_type_values(session: AsyncSession, client_type: ClientType) -> None:
    """Test both client type values."""
    client = Client(name="Test Client", type=client_type)
    session.add(client)
    await session.flush()
    await session.refresh(client)

    assert client.type == client_type


@pytest.mark.parametrize(
    "status",
    [ClientStatus.ACTIVE, ClientStatus.PAST],
)
@pytest.mark.asyncio
async def test_client_status_values(session: AsyncSession, status: ClientStatus) -> None:
    """Test both client status values."""
    client = Client(name="Test Client", type=ClientType.COMPANY, status=status)
    session.add(client)
    await session.flush()
    await session.refresh(client)

    assert client.status == status


@pytest.mark.asyncio
async def test_client_individual_type(session: AsyncSession) -> None:
    """Test creating individual client."""
    client = Client(
        name="John Doe",
        type=ClientType.INDIVIDUAL,
    )
    session.add(client)
    await session.flush()
    await session.refresh(client)

    assert client.type == ClientType.INDIVIDUAL
    assert client.name == "John Doe"


@pytest.mark.asyncio
async def test_client_relationship_with_projects(session: AsyncSession) -> None:
    """Test client-project relationship loading."""
    employer = Employer(name="Test Employer")
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project1 = Project(
        name="Project X",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        status=ProjectStatus.ACTIVE,
    )
    project2 = Project(
        name="Project Y",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        status=ProjectStatus.PAUSED,
    )
    session.add_all([project1, project2])
    await session.flush()

    # Reload with relationship
    stmt = select(Client).where(Client.id == client.id).options(selectinload(Client.projects))
    result = await session.execute(stmt)
    loaded_client = result.scalar_one()

    assert len(loaded_client.projects) == 2
    assert {p.name for p in loaded_client.projects} == {"Project X", "Project Y"}


@pytest.mark.asyncio
async def test_client_status_transition(session: AsyncSession) -> None:
    """Test transitioning client from active to past."""
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    session.add(client)
    await session.flush()
    await session.refresh(client)

    assert client.status == ClientStatus.ACTIVE

    client.status = ClientStatus.PAST
    await session.flush()
    await session.refresh(client)

    assert client.status == ClientStatus.PAST


@pytest.mark.asyncio
async def test_client_name_indexing(session: AsyncSession) -> None:
    """Test that client names are indexed and queryable."""
    client1 = Client(name="Acme Corp", type=ClientType.COMPANY)
    client2 = Client(name="Beta Inc", type=ClientType.COMPANY)
    client3 = Client(name="Acme Industries", type=ClientType.COMPANY)
    session.add_all([client1, client2, client3])
    await session.flush()

    # Query by name pattern
    stmt = select(Client).where(Client.name.like("Acme%"))
    result = await session.execute(stmt)
    clients = result.scalars().all()

    assert len(clients) == 2
    assert {c.name for c in clients} == {"Acme Corp", "Acme Industries"}
