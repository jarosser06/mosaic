"""Integration tests for log_work_session MCP tool.

Tests end-to-end work session logging through real MCP server,
including validation, duration calculation, and database persistence.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.project import Project
from src.mosaic.schemas.work_session import LogWorkSessionInput
from src.mosaic.tools.logging_tools import log_work_session


class TestLogWorkSessionTool:
    """Test log_work_session tool with real MCP server."""

    @pytest.mark.asyncio
    async def test_log_work_session_basic(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test logging a basic work session through real MCP tool."""
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
            project_id=project.id,
            description="Implemented feature X",
        )

        # Call REAL tool with REAL MCP context
        result = await log_work_session(input_data, mcp_client)

        # Verify result
        assert result.id is not None
        assert result.project_id == project.id
        assert result.duration_hours == Decimal("8.0")
        assert result.description == "Implemented feature X"
        assert result.privacy_level == PrivacyLevel.PRIVATE

        # Verify database persistence
        from src.mosaic.repositories.work_session_repository import WorkSessionRepository

        repo = WorkSessionRepository(test_session)
        fetched = await repo.get_by_id(result.id)
        assert fetched is not None
        assert fetched.project_id == project.id
        assert fetched.summary == "Implemented feature X"

    @pytest.mark.asyncio
    async def test_log_work_session_with_half_hour_rounding(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test work session with half-hour rounding."""
        # 2 hours 15 minutes -> should round to 2.5 hours
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 11, 15, tzinfo=timezone.utc),
            project_id=project.id,
        )

        result = await log_work_session(input_data, mcp_client)

        assert result.duration_hours == Decimal("2.5")

    @pytest.mark.asyncio
    async def test_log_work_session_with_31_minutes_rounds_up(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that 31 minutes rounds up to 1.0 hour."""
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 9, 31, tzinfo=timezone.utc),
            project_id=project.id,
        )

        result = await log_work_session(input_data, mcp_client)

        assert result.duration_hours == Decimal("1.0")

    @pytest.mark.asyncio
    async def test_log_work_session_with_privacy_level(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test logging work session with specific privacy level."""
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=project.id,
            privacy_level=PrivacyLevel.PUBLIC,
        )

        result = await log_work_session(input_data, mcp_client)

        assert result.privacy_level == PrivacyLevel.PUBLIC

    @pytest.mark.asyncio
    async def test_log_work_session_with_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test logging work session with tags."""
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=project.id,
            tags=["backend", "api", "authentication"],
        )

        result = await log_work_session(input_data, mcp_client)

        assert result.tags == ["backend", "api", "authentication"]

    @pytest.mark.asyncio
    async def test_log_work_session_invalid_project_id(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test logging work session with non-existent project."""
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=99999,  # Non-existent project
        )

        with pytest.raises(Exception):
            await log_work_session(input_data, mcp_client)

    @pytest.mark.asyncio
    async def test_log_work_session_end_before_start(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test logging work session with end_time before start_time."""
        with pytest.raises(ValidationError):
            LogWorkSessionInput(
                start_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                project_id=project.id,
            )

    @pytest.mark.asyncio
    async def test_log_work_session_timestamps_created(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that created_at and updated_at timestamps are set."""
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=project.id,
        )

        result = await log_work_session(input_data, mcp_client)

        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.created_at == result.updated_at

    @pytest.mark.asyncio
    async def test_log_work_session_persisted_to_database(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test that work session is persisted to database."""
        from src.mosaic.repositories.work_session_repository import WorkSessionRepository

        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=project.id,
            description="Test work",
        )

        result = await log_work_session(input_data, mcp_client)

        # Verify it's in the database
        repo = WorkSessionRepository(test_session)
        fetched = await repo.get_by_id(result.id)

        assert fetched is not None
        assert fetched.project_id == project.id
        # The model uses 'summary' field, not 'description'
        assert fetched.summary == "Test work"
