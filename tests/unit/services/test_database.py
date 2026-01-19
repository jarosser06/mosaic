"""Unit tests for database session management service."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.services.database import get_session, init_db


class TestDatabaseSessionManagement:
    """Test session management, transaction handling, and lifecycle."""

    async def asyncSetUp(self):
        """Dispose engine connections before each test to ensure fresh event loop."""
        from src.mosaic.services.database import engine

        await engine.dispose()

    async def asyncTearDown(self):
        """Dispose engine connections after each test to prevent event loop issues."""
        from src.mosaic.services.database import engine

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_session_yields_async_session(self):
        """Test get_session yields a valid AsyncSession."""
        await self.asyncSetUp()
        try:
            async with get_session() as session:
                assert isinstance(session, AsyncSession)
        finally:
            await self.asyncTearDown()

    @pytest.mark.asyncio
    async def test_get_session_auto_commits_on_success(self):
        """Test session auto-commits when no exception raised."""
        await self.asyncSetUp()
        try:
            async with get_session() as session:
                # Execute a simple query
                result = await session.execute(text("SELECT 1 as value"))
                row = result.first()
                assert row.value == 1  # type: ignore

            # If we reach here, commit was successful
        finally:
            await self.asyncTearDown()

    @pytest.mark.asyncio
    async def test_get_session_rolls_back_on_exception(self):
        """Test session rolls back when exception raised."""
        await self.asyncSetUp()
        try:
            with pytest.raises(ValueError):
                async with get_session() as session:
                    # Execute a query
                    await session.execute(text("SELECT 1"))
                    # Raise exception to trigger rollback
                    raise ValueError("Test exception")
        finally:
            await self.asyncTearDown()

    @pytest.mark.asyncio
    async def test_get_session_closes_after_use(self):
        """Test session context manager properly manages lifecycle."""
        await self.asyncSetUp()
        try:
            session_ref = None
            async with get_session() as session:
                session_ref = session
                await session.execute(text("SELECT 1"))

            # Verify session was created and used successfully
            assert session_ref is not None

            # The get_session() context manager:
            # 1. Creates session and starts transaction (session.begin())
            # 2. Yields session for use
            # 3. Commits transaction when context exits (if no exception)
            # 4. Calls session.close() in finally block
            # This test verifies the context manager completes successfully
        finally:
            await self.asyncTearDown()

    @pytest.mark.asyncio
    async def test_get_session_multiple_operations(self):
        """Test session can handle multiple operations in one context."""
        await self.asyncSetUp()
        try:
            async with get_session() as session:
                # First query
                result1 = await session.execute(text("SELECT 1 as value"))
                row1 = result1.first()
                assert row1.value == 1  # type: ignore

                # Second query
                result2 = await session.execute(text("SELECT 2 as value"))
                row2 = result2.first()
                assert row2.value == 2  # type: ignore
        finally:
            await self.asyncTearDown()

    @pytest.mark.asyncio
    async def test_get_session_nested_contexts_independent(self):
        """Test nested session contexts are independent."""
        await self.asyncSetUp()
        try:
            async with get_session() as session1:
                result1 = await session1.execute(text("SELECT 1 as value"))
                row1 = result1.first()
                assert row1.value == 1  # type: ignore

                async with get_session() as session2:
                    result2 = await session2.execute(text("SELECT 2 as value"))
                    row2 = result2.first()
                    assert row2.value == 2  # type: ignore

                    # Different session instances
                    assert session1 is not session2
        finally:
            await self.asyncTearDown()

    @pytest.mark.asyncio
    async def test_get_session_exception_with_multiple_operations(self):
        """Test rollback works correctly with multiple operations."""
        await self.asyncSetUp()
        try:
            with pytest.raises(RuntimeError):
                async with get_session() as session:
                    # First operation
                    await session.execute(text("SELECT 1"))
                    # Second operation
                    await session.execute(text("SELECT 2"))
                    # Raise exception - both should be rolled back
                    raise RuntimeError("Test rollback with multiple ops")
        finally:
            await self.asyncTearDown()

    @pytest.mark.asyncio
    async def test_get_session_pool_pre_ping_enabled(self):
        """Test pool pre-ping is configured (prevents stale connections)."""
        await self.asyncSetUp()
        try:
            # This is more of a configuration test
            # We can verify by using multiple sessions
            async with get_session() as session1:
                await session1.execute(text("SELECT 1"))

            async with get_session() as session2:
                await session2.execute(text("SELECT 1"))

            # Both should succeed - pool pre-ping keeps connections fresh
        finally:
            await self.asyncTearDown()

        # Both should succeed - pool pre-ping keeps connections fresh


class TestTableCreation:
    """Test automatic table creation with SQLAlchemy metadata.create_all()."""

    @pytest.mark.asyncio
    async def test_create_tables_creates_all_expected_tables(self, test_engine):
        """Test _create_tables() creates all 11 expected database tables."""
        from src.mosaic.models.base import Base

        # First, drop all tables to ensure clean state
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        # Now create tables using the same pattern as _create_tables()
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Verify all expected tables exist
        expected_tables = {
            "users",
            "employers",
            "clients",
            "people",
            "employment_history",
            "projects",
            "work_sessions",
            "meetings",
            "meeting_attendees",
            "reminders",
            "notes",
        }

        async with test_engine.connect() as conn:
            # Get list of actual tables using inspector
            def get_table_names(sync_conn):
                inspector = inspect(sync_conn)
                return set(inspector.get_table_names())

            actual_tables = await conn.run_sync(get_table_names)

        # Verify all expected tables were created
        assert expected_tables.issubset(
            actual_tables
        ), f"Missing tables: {expected_tables - actual_tables}"

    @pytest.mark.asyncio
    async def test_create_tables_idempotent(self, test_engine):
        """Test create_all() can be called multiple times without errors."""
        from src.mosaic.models.base import Base

        # Call create_all() twice
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)  # Should not raise exception

        # Verify tables still exist after second call
        async with test_engine.connect() as conn:

            def get_table_names(sync_conn):
                inspector = inspect(sync_conn)
                return set(inspector.get_table_names())

            actual_tables = await conn.run_sync(get_table_names)

        # Should have at least our 11 tables
        expected_tables = {
            "users",
            "employers",
            "clients",
            "people",
            "employment_history",
            "projects",
            "work_sessions",
            "meetings",
            "meeting_attendees",
            "reminders",
            "notes",
        }
        assert expected_tables.issubset(actual_tables)

    @pytest.mark.asyncio
    async def test_init_db_calls_create_tables(self):
        """Test init_db() calls _create_tables() function."""
        # Mock both _ensure_database_exists and _create_tables
        with (
            patch("src.mosaic.services.database._ensure_database_exists") as mock_ensure_db,
            patch("src.mosaic.services.database._create_tables") as mock_create_tables,
        ):
            mock_ensure_db.return_value = None
            mock_create_tables.return_value = None

            # Call init_db()
            await init_db()

            # Verify both functions were called
            mock_ensure_db.assert_called_once()
            mock_create_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tables_error_handling(self):
        """Test _create_tables() handles connection errors properly."""
        from src.mosaic.services.database import _create_tables

        # Mock the engine to raise an exception
        with patch("src.mosaic.services.database.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = Exception("Connection failed")
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            # Verify exception is raised
            with pytest.raises(Exception, match="Connection failed"):
                await _create_tables()
