"""Verification tests for test fixtures implementation."""

import pytest


@pytest.mark.asyncio
async def test_mcp_client_has_real_app_context(mcp_client, test_app_context):
    """Verify mcp_client uses real AppContext."""

    # Access app context through mcp_client
    ctx_app_context = mcp_client.request_context.lifespan_context

    # Should be the exact same object as test_app_context
    assert ctx_app_context is test_app_context
    assert ctx_app_context.engine is not None
    assert ctx_app_context.session_factory is not None
    assert ctx_app_context.scheduler is not None


@pytest.mark.asyncio
async def test_test_engine_configured(test_engine):
    """Verify test database engine is configured."""

    # Check engine URL is valid
    engine_url = str(test_engine.url)
    assert engine_url is not None
    # Can be either SQLite or PostgreSQL
    assert ("sqlite" in engine_url) or ("postgresql" in engine_url)


@pytest.mark.asyncio
async def test_entity_fixtures_in_test_db(test_session, employer, client, project):
    """Verify entity fixtures are created in test database."""

    assert employer.id is not None
    assert client.id is not None
    assert project.id is not None

    # Verify they're in the session
    assert employer in test_session
    assert client in test_session
    assert project in test_session


@pytest.mark.asyncio
async def test_database_isolation(test_session, project):
    """Verify each test gets a fresh database."""

    from datetime import date, datetime, timezone
    from decimal import Decimal

    from src.mosaic.models.work_session import WorkSession
    from src.mosaic.repositories.work_session_repository import WorkSessionRepository

    # Create work session
    ws = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("1.0"),
    )
    test_session.add(ws)
    await test_session.flush()

    # Count work sessions
    repo = WorkSessionRepository(test_session)
    all_sessions = await repo.list_all()
    count_before = len(all_sessions)

    # This test should not see data from other tests
    # (In a fresh test, should only see the one we just created)
    assert count_before == 1


@pytest.mark.asyncio
async def test_database_isolation_second_test(test_session, project):
    """Second test to verify isolation from previous test."""

    from src.mosaic.repositories.work_session_repository import WorkSessionRepository

    # Should start with empty database (no data from previous test)
    repo = WorkSessionRepository(test_session)
    all_sessions = await repo.list_all()

    # Should be 0 because previous test rolled back
    assert len(all_sessions) == 0
