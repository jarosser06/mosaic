"""Tests for Employer model."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.project import Project, ProjectStatus


@pytest.mark.asyncio
async def test_employer_creation_minimal(session: AsyncSession) -> None:
    """Test creating employer with minimal required fields."""
    employer = Employer(name="Test Corp")
    session.add(employer)
    await session.flush()
    await session.refresh(employer)

    assert employer.id is not None
    assert employer.name == "Test Corp"
    assert employer.is_current is False
    assert employer.is_self is False
    assert employer.contact_info is None
    assert employer.notes is None
    assert employer.created_at is not None
    assert employer.updated_at is not None


@pytest.mark.asyncio
async def test_employer_creation_full(session: AsyncSession) -> None:
    """Test creating employer with all fields populated."""
    employer = Employer(
        name="Acme Corporation",
        is_current=True,
        is_self=False,
        contact_info="hr@acme.com",
        notes="Great company to work for",
    )
    session.add(employer)
    await session.flush()
    await session.refresh(employer)

    assert employer.name == "Acme Corporation"
    assert employer.is_current is True
    assert employer.is_self is False
    assert employer.contact_info == "hr@acme.com"
    assert employer.notes == "Great company to work for"


@pytest.mark.asyncio
async def test_employer_self_employed(session: AsyncSession) -> None:
    """Test creating self-employed employer."""
    employer = Employer(
        name="Self",
        is_current=True,
        is_self=True,
    )
    session.add(employer)
    await session.flush()
    await session.refresh(employer)

    assert employer.is_self is True
    assert employer.is_current is True


@pytest.mark.asyncio
async def test_employer_relationship_with_projects(session: AsyncSession) -> None:
    """Test employer-project relationship loading."""
    employer = Employer(name="Test Employer", is_current=True)
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    session.add_all([employer, client])
    await session.flush()

    project1 = Project(
        name="Project Alpha",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        status=ProjectStatus.ACTIVE,
    )
    project2 = Project(
        name="Project Beta",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        status=ProjectStatus.COMPLETED,
    )
    session.add_all([project1, project2])
    await session.flush()

    # Reload with relationship
    stmt = (
        select(Employer).where(Employer.id == employer.id).options(selectinload(Employer.projects))
    )
    result = await session.execute(stmt)
    loaded_employer = result.scalar_one()

    assert len(loaded_employer.projects) == 2
    assert {p.name for p in loaded_employer.projects} == {"Project Alpha", "Project Beta"}


@pytest.mark.asyncio
async def test_employer_update_flags(session: AsyncSession) -> None:
    """Test updating employer flags."""
    employer = Employer(name="Old Employer", is_current=True)
    session.add(employer)
    await session.flush()
    await session.refresh(employer)

    employer.is_current = False
    await session.flush()
    await session.refresh(employer)

    assert employer.is_current is False


@pytest.mark.asyncio
async def test_employer_name_indexing(session: AsyncSession) -> None:
    """Test that employer names are indexed and queryable."""
    employer1 = Employer(name="Alpha Corp")
    employer2 = Employer(name="Beta Corp")
    employer3 = Employer(name="Alpha Industries")
    session.add_all([employer1, employer2, employer3])
    await session.flush()

    # Query by name
    stmt = select(Employer).where(Employer.name.like("Alpha%"))
    result = await session.execute(stmt)
    employers = result.scalars().all()

    assert len(employers) == 2
    assert {e.name for e in employers} == {"Alpha Corp", "Alpha Industries"}
