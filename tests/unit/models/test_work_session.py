"""Tests for WorkSession model (simplified: date + duration only)."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.mosaic.models.base import ClientType, PrivacyLevel
from src.mosaic.models.client import Client
from src.mosaic.models.employer import Employer
from src.mosaic.models.project import Project
from src.mosaic.models.work_session import WorkSession


@pytest.mark.asyncio
async def test_work_session_creation_minimal(session: AsyncSession, project: Project) -> None:
    """Test creating work session with minimal required fields."""
    work_date = date(2024, 1, 15)

    work_session = WorkSession(
        project_id=project.id,
        date=work_date,
        duration_hours=Decimal("1.5"),
    )
    session.add(work_session)
    await session.flush()
    await session.refresh(work_session)

    assert work_session.id is not None
    assert work_session.project_id == project.id
    assert work_session.date == work_date
    assert work_session.duration_hours == Decimal("1.5")
    assert work_session.privacy_level == PrivacyLevel.PRIVATE
    assert work_session.summary is None
    assert work_session.created_at is not None
    assert work_session.updated_at is not None


@pytest.mark.asyncio
async def test_work_session_creation_full(session: AsyncSession, project: Project) -> None:
    """Test creating work session with all fields populated."""
    work_session = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("3.0"),
        summary="Implemented user authentication module",
        privacy_level=PrivacyLevel.INTERNAL,
        tags=["backend", "authentication"],
    )
    session.add(work_session)
    await session.flush()
    await session.refresh(work_session)

    assert work_session.summary == "Implemented user authentication module"
    assert work_session.privacy_level == PrivacyLevel.INTERNAL
    assert work_session.duration_hours == Decimal("3.0")
    assert work_session.tags == ["backend", "authentication"]


@pytest.mark.parametrize(
    "privacy_level",
    [PrivacyLevel.PUBLIC, PrivacyLevel.INTERNAL, PrivacyLevel.PRIVATE],
)
@pytest.mark.asyncio
async def test_work_session_privacy_levels(
    session: AsyncSession, project: Project, privacy_level: PrivacyLevel
) -> None:
    """Test all privacy level values for work sessions."""
    work_session = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("1.0"),
        privacy_level=privacy_level,
    )
    session.add(work_session)
    await session.flush()
    await session.refresh(work_session)

    assert work_session.privacy_level == privacy_level


@pytest.mark.parametrize(
    "duration",
    [
        Decimal("0.1"),  # Very small duration
        Decimal("0.5"),  # 30 minutes
        Decimal("1.0"),  # 1 hour
        Decimal("2.5"),  # 2.5 hours
        Decimal("8.0"),  # Full day
        Decimal("12.5"),  # Long session
        Decimal("16.0"),  # Very long session
        Decimal("24.0"),  # Max duration
    ],
)
@pytest.mark.asyncio
async def test_work_session_duration_values(
    session: AsyncSession, project: Project, duration: Decimal
) -> None:
    """Test various duration values from very small to maximum."""
    work_session = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=duration,
    )
    session.add(work_session)
    await session.flush()
    await session.refresh(work_session)

    assert work_session.duration_hours == duration


@pytest.mark.asyncio
async def test_work_session_relationship_with_project(
    session: AsyncSession, project: Project
) -> None:
    """Test work session-project relationship loading."""
    work_session = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("1.0"),
    )
    session.add(work_session)
    await session.flush()

    # Reload with relationship
    stmt = (
        select(WorkSession)
        .where(WorkSession.id == work_session.id)
        .options(selectinload(WorkSession.project))
    )
    result = await session.execute(stmt)
    loaded_session = result.scalar_one()

    assert loaded_session.project.name == project.name
    assert loaded_session.project.id == project.id


@pytest.mark.asyncio
async def test_work_session_date_indexing(session: AsyncSession, project: Project) -> None:
    """Test that work session dates are indexed and queryable."""
    ws1 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("1.0"),
    )
    ws2 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 16),
        duration_hours=Decimal("1.0"),
    )
    ws3 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("2.0"),
    )
    session.add_all([ws1, ws2, ws3])
    await session.flush()

    # Query by date
    stmt = select(WorkSession).where(WorkSession.date == date(2024, 1, 15))
    result = await session.execute(stmt)
    sessions = result.scalars().all()

    assert len(sessions) == 2


@pytest.mark.asyncio
async def test_work_session_project_date_composite_index(
    session: AsyncSession, project: Project
) -> None:
    """Test composite index on project_id and date."""
    employer = Employer(name="Other Employer")
    client = Client(name="Other Client", type=ClientType.COMPANY)
    session.add_all([employer, client])
    await session.flush()

    project2 = Project(
        name="Other Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
    )
    session.add(project2)
    await session.flush()

    ws1 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("1.0"),
    )
    ws2 = WorkSession(
        project_id=project2.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("1.0"),
    )
    session.add_all([ws1, ws2])
    await session.flush()

    # Query by project_id and date
    stmt = select(WorkSession).where(
        WorkSession.project_id == project.id, WorkSession.date == date(2024, 1, 15)
    )
    result = await session.execute(stmt)
    sessions = result.scalars().all()

    assert len(sessions) == 1
    assert sessions[0].id == ws1.id


@pytest.mark.asyncio
async def test_work_session_summary_optional(session: AsyncSession, project: Project) -> None:
    """Test work session with no summary."""
    work_session = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("1.0"),
        summary=None,
    )
    session.add(work_session)
    await session.flush()
    await session.refresh(work_session)

    assert work_session.summary is None


@pytest.mark.asyncio
async def test_work_session_decimal_precision(session: AsyncSession, project: Project) -> None:
    """Test that duration_hours maintains decimal precision (1 decimal place)."""
    work_session = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        duration_hours=Decimal("2.3"),
    )
    session.add(work_session)
    await session.flush()
    await session.refresh(work_session)

    # Database uses Numeric(4, 1) = 1 decimal place
    assert work_session.duration_hours == Decimal("2.3")
    assert isinstance(work_session.duration_hours, Decimal)


@pytest.mark.asyncio
async def test_work_session_leap_day_edge_case(session: AsyncSession, project: Project) -> None:
    """Test work session on leap day (2024-02-29)."""
    leap_day = date(2024, 2, 29)  # 2024 is a leap year

    work_session = WorkSession(
        project_id=project.id,
        date=leap_day,
        duration_hours=Decimal("8.0"),
        summary="Work on leap day",
    )
    session.add(work_session)
    await session.flush()
    await session.refresh(work_session)

    assert work_session.date == leap_day
    assert work_session.duration_hours == Decimal("8.0")
