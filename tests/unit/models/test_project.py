"""Tests for Project model."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.mosaic.models.base import ClientStatus, ClientType, ProjectStatus
from src.mosaic.models.client import Client
from src.mosaic.models.employer import Employer
from src.mosaic.models.project import Project


@pytest.mark.asyncio
async def test_project_creation_minimal(session: AsyncSession) -> None:
    """Test creating project with minimal required fields."""
    employer = Employer(name="Test Employer")
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Test Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
    )
    session.add(project)
    await session.flush()
    await session.refresh(project)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.on_behalf_of_id == employer.id
    assert project.client_id == client.id
    assert project.status == ProjectStatus.ACTIVE
    assert project.description is None
    assert project.start_date is None
    assert project.end_date is None
    assert project.created_at is not None
    assert project.updated_at is not None


@pytest.mark.asyncio
async def test_project_creation_full(session: AsyncSession) -> None:
    """Test creating project with all fields populated."""
    employer = Employer(name="My Company")
    client = Client(name="Big Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Enterprise Portal",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        description="Build modern web portal",
        status=ProjectStatus.ACTIVE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )
    session.add(project)
    await session.flush()
    await session.refresh(project)

    assert project.name == "Enterprise Portal"
    assert project.description == "Build modern web portal"
    assert project.status == ProjectStatus.ACTIVE
    assert project.start_date == date(2024, 1, 1)
    assert project.end_date == date(2024, 12, 31)


@pytest.mark.parametrize(
    "status",
    [ProjectStatus.ACTIVE, ProjectStatus.PAUSED, ProjectStatus.COMPLETED],
)
@pytest.mark.asyncio
async def test_project_status_values(session: AsyncSession, status: ProjectStatus) -> None:
    """Test all project status values."""
    employer = Employer(name="Test Employer")
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Test Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        status=status,
    )
    session.add(project)
    await session.flush()
    await session.refresh(project)

    assert project.status == status


@pytest.mark.asyncio
async def test_project_relationship_with_employer(session: AsyncSession) -> None:
    """Test project-employer relationship loading."""
    employer = Employer(name="Test Employer", is_current=True)
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Test Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
    )
    session.add(project)
    await session.flush()

    # Reload with relationship
    stmt = select(Project).where(Project.id == project.id).options(selectinload(Project.employer))
    result = await session.execute(stmt)
    loaded_project = result.scalar_one()

    assert loaded_project.employer.name == "Test Employer"
    assert loaded_project.employer.is_current is True


@pytest.mark.asyncio
async def test_project_relationship_with_client(session: AsyncSession) -> None:
    """Test project-client relationship loading."""
    employer = Employer(name="Test Employer")
    client = Client(name="Big Corp", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Test Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
    )
    session.add(project)
    await session.flush()

    # Reload with relationship
    stmt = select(Project).where(Project.id == project.id).options(selectinload(Project.client))
    result = await session.execute(stmt)
    loaded_project = result.scalar_one()

    assert loaded_project.client.name == "Big Corp"
    assert loaded_project.client.status == ClientStatus.ACTIVE


@pytest.mark.asyncio
async def test_project_status_transition(session: AsyncSession) -> None:
    """Test transitioning project through statuses."""
    employer = Employer(name="Test Employer")
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Test Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        status=ProjectStatus.ACTIVE,
    )
    session.add(project)
    await session.flush()

    project.status = ProjectStatus.PAUSED
    await session.flush()
    await session.refresh(project)
    assert project.status == ProjectStatus.PAUSED

    project.status = ProjectStatus.COMPLETED
    await session.flush()
    await session.refresh(project)
    assert project.status == ProjectStatus.COMPLETED


@pytest.mark.asyncio
async def test_project_date_range(session: AsyncSession) -> None:
    """Test project with start and end dates."""
    employer = Employer(name="Test Employer")
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Q1 Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
    )
    session.add(project)
    await session.flush()
    await session.refresh(project)

    assert project.start_date == date(2024, 1, 1)
    assert project.end_date == date(2024, 3, 31)


@pytest.mark.asyncio
async def test_project_ongoing_no_end_date(session: AsyncSession) -> None:
    """Test project with start date but no end date (ongoing)."""
    employer = Employer(name="Test Employer")
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project = Project(
        name="Ongoing Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        start_date=date(2024, 1, 1),
        end_date=None,
    )
    session.add(project)
    await session.flush()
    await session.refresh(project)

    assert project.start_date is not None
    assert project.end_date is None


@pytest.mark.asyncio
async def test_project_name_indexing(session: AsyncSession) -> None:
    """Test that project names are indexed and queryable."""
    employer = Employer(name="Test Employer")
    client = Client(name="Test Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project1 = Project(name="Alpha Project", on_behalf_of_id=employer.id, client_id=client.id)
    project2 = Project(name="Beta Project", on_behalf_of_id=employer.id, client_id=client.id)
    project3 = Project(name="Alpha Initiative", on_behalf_of_id=employer.id, client_id=client.id)
    session.add_all([project1, project2, project3])
    await session.flush()

    # Query by name pattern
    stmt = select(Project).where(Project.name.like("Alpha%"))
    result = await session.execute(stmt)
    projects = result.scalars().all()

    assert len(projects) == 2
    assert {p.name for p in projects} == {"Alpha Project", "Alpha Initiative"}
