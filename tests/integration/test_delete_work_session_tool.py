"""Integration tests for delete_work_session MCP tool.

Tests end-to-end work session deletion through MCP tool interface,
including validation, error handling, and database persistence.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.project import Project
from src.mosaic.models.work_session import WorkSession
from src.mosaic.repositories.work_session_repository import WorkSessionRepository
from src.mosaic.schemas.work_session import (
    DeleteWorkSessionInput,
    LogWorkSessionInput,
)
from src.mosaic.tools.logging_tools import delete_work_session, log_work_session


class TestDeleteWorkSessionTool:
    """Test delete_work_session tool with real MCP server."""

    @pytest.mark.asyncio
    async def test_delete_work_session_success(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test successfully deleting a work session (create → delete → verify)."""
        # Create a work session
        create_input = LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("8.0"),
            project_id=project.id,
            description="Work to be deleted",
        )
        created = await log_work_session(create_input, mcp_client)
        work_session_id = created.id

        # Verify it exists
        repo = WorkSessionRepository(test_session)
        session_before = await repo.get_by_id(work_session_id)
        assert session_before is not None

        # Delete the work session
        delete_input = DeleteWorkSessionInput(work_session_id=work_session_id)
        result = await delete_work_session(delete_input, mcp_client)

        # Verify deletion succeeded
        assert result.success is True
        assert str(work_session_id) in result.message
        assert "deleted" in result.message.lower()

        # Verify it's removed from database
        session_after = await repo.get_by_id(work_session_id)
        assert session_after is None

    @pytest.mark.asyncio
    async def test_delete_work_session_not_found(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test deleting a non-existent work session raises ValueError."""
        # Try to delete non-existent work session
        delete_input = DeleteWorkSessionInput(work_session_id=99999)

        with pytest.raises(ValueError) as exc_info:
            await delete_work_session(delete_input, mcp_client)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_work_session_verify_database_persistence(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that deleted work session is actually removed from database."""
        # Create work session
        create_input = LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("4.0"),
            project_id=project.id,
            description="Test deletion persistence",
        )
        created = await log_work_session(create_input, mcp_client)

        # Delete it
        delete_input = DeleteWorkSessionInput(work_session_id=created.id)
        await delete_work_session(delete_input, mcp_client)

        # Verify no record in database
        stmt = select(WorkSession).where(WorkSession.id == created.id)
        result = await test_session.execute(stmt)
        fetched = result.scalar_one_or_none()

        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_work_session_output_structure(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that DeleteWorkSessionOutput has correct structure."""
        # Create and delete a work session
        create_input = LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("2.0"),
            project_id=project.id,
        )
        created = await log_work_session(create_input, mcp_client)

        delete_input = DeleteWorkSessionInput(work_session_id=created.id)
        result = await delete_work_session(delete_input, mcp_client)

        # Verify output structure
        assert hasattr(result, "success")
        assert hasattr(result, "message")
        assert isinstance(result.success, bool)
        assert isinstance(result.message, str)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_work_session_with_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test deleting a work session that has tags."""
        # Create work session with tags
        create_input = LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("3.0"),
            project_id=project.id,
            description="Work with tags",
            tags=["backend", "testing"],
        )
        created = await log_work_session(create_input, mcp_client)

        # Delete it
        delete_input = DeleteWorkSessionInput(work_session_id=created.id)
        result = await delete_work_session(delete_input, mcp_client)

        assert result.success is True

        # Verify deletion
        repo = WorkSessionRepository(test_session)
        deleted = await repo.get_by_id(created.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_work_session_does_not_affect_other_sessions(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that deleting one work session doesn't affect others."""
        # Create two work sessions
        create_input1 = LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("4.0"),
            project_id=project.id,
            description="Session 1",
        )
        session1 = await log_work_session(create_input1, mcp_client)

        create_input2 = LogWorkSessionInput(
            date=date(2026, 1, 16),
            duration_hours=Decimal("5.0"),
            project_id=project.id,
            description="Session 2",
        )
        session2 = await log_work_session(create_input2, mcp_client)

        # Delete first session
        delete_input = DeleteWorkSessionInput(work_session_id=session1.id)
        await delete_work_session(delete_input, mcp_client)

        # Verify first is deleted, second remains
        repo = WorkSessionRepository(test_session)
        deleted = await repo.get_by_id(session1.id)
        remaining = await repo.get_by_id(session2.id)

        assert deleted is None
        assert remaining is not None
        assert remaining.summary == "Session 2"

    @pytest.mark.asyncio
    async def test_delete_work_session_idempotency(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that deleting an already-deleted work session raises ValueError."""
        # Create and delete a work session
        create_input = LogWorkSessionInput(
            date=date(2026, 1, 15),
            duration_hours=Decimal("2.0"),
            project_id=project.id,
        )
        created = await log_work_session(create_input, mcp_client)

        delete_input = DeleteWorkSessionInput(work_session_id=created.id)
        await delete_work_session(delete_input, mcp_client)

        # Try to delete again
        with pytest.raises(ValueError) as exc_info:
            await delete_work_session(delete_input, mcp_client)

        assert "not found" in str(exc_info.value).lower()
