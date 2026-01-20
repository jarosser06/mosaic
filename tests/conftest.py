"""Global pytest fixtures for all tests."""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project, ProjectStatus

# Import all fixtures from fixtures package
from tests.fixtures import (
    mcp_client,
    mcp_server,
    test_app_context,
    test_engine,
    test_session,
    test_session_factory,
)

# Make fixtures available to all tests
__all__ = [
    "test_engine",
    "test_session_factory",
    "test_session",
    "test_app_context",
    "mcp_server",
    "mcp_client",
]


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for pytest-asyncio."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


# ============================================================================
# Backwards Compatibility Alias
# ============================================================================


@pytest.fixture
async def session(test_session: AsyncSession) -> AsyncSession:
    """Alias for test_session to maintain backwards compatibility with unit tests."""
    return test_session


@pytest.fixture
async def app_context_fixture(test_app_context):
    """Alias for test_app_context to maintain compatibility with integration tests."""
    return test_app_context


# ============================================================================
# Entity Fixtures (use test_session, not session)
# ============================================================================


@pytest.fixture
async def employer(test_session: AsyncSession) -> Employer:
    """Create test employer."""
    employer = Employer(
        name="Test Corp",
        is_current=True,
    )
    test_session.add(employer)
    await test_session.commit()
    await test_session.refresh(employer)
    return employer


@pytest.fixture
async def client(test_session: AsyncSession) -> Client:
    """Create test client."""
    client = Client(
        name="Test Client Inc",
        type=ClientType.COMPANY,
        status=ClientStatus.ACTIVE,
    )
    test_session.add(client)
    await test_session.commit()
    await test_session.refresh(client)
    return client


@pytest.fixture
async def project(test_session: AsyncSession, employer: Employer, client: Client) -> Project:
    """Create test project."""
    project = Project(
        name="Test Project",
        on_behalf_of_id=employer.id,
        client_id=client.id,
        description="Test project description",
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)
    return project


@pytest.fixture
async def person(test_session: AsyncSession) -> Person:
    """Create test person."""
    person = Person(
        full_name="John Doe",
        email="john@example.com",
    )
    test_session.add(person)
    await test_session.commit()
    await test_session.refresh(person)
    return person


@pytest.fixture
def sample_datetime() -> datetime:
    """Provide a consistent datetime for tests."""
    return datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_date() -> date:
    """Provide a consistent date for tests."""
    return date(2024, 1, 15)
