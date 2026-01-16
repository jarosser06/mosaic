"""Integration tests for log_meeting MCP tool.

Tests end-to-end meeting logging through real MCP server,
including attendee management, project association, and work session
auto-generation.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import PrivacyLevel
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project
from src.mosaic.schemas.meeting import LogMeetingInput
from src.mosaic.tools.logging_tools import log_meeting


class TestLogMeetingTool:
    """Test log_meeting tool with real MCP server."""

    @pytest.mark.asyncio
    async def test_log_meeting_basic(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test logging a basic meeting without project through real MCP tool."""
        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Team Standup",
            description="Daily standup meeting",
        )

        # Call REAL tool with REAL MCP context
        result = await log_meeting(input_data, mcp_client)

        # Verify result
        assert result.id is not None
        assert result.title == "Team Standup"
        assert result.description == "Daily standup meeting"
        assert result.project_id is None

        # Verify database persistence
        from src.mosaic.repositories.meeting_repository import MeetingRepository

        repo = MeetingRepository(test_session)
        fetched = await repo.get_by_id(result.id)
        assert fetched is not None
        assert fetched.title == "Team Standup"

    @pytest.mark.asyncio
    async def test_log_meeting_with_attendees(
        self,
        mcp_client,
        test_session: AsyncSession,
        person: Person,
    ):
        """Test logging meeting with attendees."""
        # Create another person
        person2 = Person(full_name="Jane Smith", email="jane@example.com")
        test_session.add(person2)
        await test_session.commit()
        await test_session.refresh(person2)

        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Sprint Planning",
            attendees=[person.id, person2.id],
        )

        result = await log_meeting(input_data, mcp_client)

        assert result.id is not None
        assert len(result.attendees) == 2
        assert person.id in result.attendees
        assert person2.id in result.attendees

    @pytest.mark.asyncio
    async def test_log_meeting_with_project(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test logging meeting with project association."""
        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Project Kickoff",
            project_id=project.id,
        )

        result = await log_meeting(input_data, mcp_client)

        assert result.id is not None
        assert result.project_id == project.id

    @pytest.mark.asyncio
    async def test_log_meeting_with_privacy_level(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test logging meeting with specific privacy level."""
        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Client Meeting",
            privacy_level=PrivacyLevel.INTERNAL,
        )

        result = await log_meeting(input_data, mcp_client)

        assert result.privacy_level == PrivacyLevel.INTERNAL

    @pytest.mark.asyncio
    async def test_log_meeting_with_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test logging meeting with tags."""
        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Architecture Review",
            tags=["planning", "architecture", "team"],
        )

        result = await log_meeting(input_data, mcp_client)

        assert result.tags == ["planning", "architecture", "team"]

    @pytest.mark.asyncio
    async def test_log_meeting_end_before_start(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test logging meeting with end_time before start_time."""
        with pytest.raises(ValidationError):
            LogMeetingInput(
                start_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
                end_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                title="Invalid Meeting",
            )

    @pytest.mark.asyncio
    async def test_log_meeting_invalid_project_id(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test logging meeting with non-existent project."""
        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Meeting",
            project_id=99999,  # Non-existent project
        )

        with pytest.raises(Exception):
            await log_meeting(input_data, mcp_client)

    @pytest.mark.asyncio
    async def test_log_meeting_timestamps_created(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test that created_at and updated_at timestamps are set."""
        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Test Meeting",
        )

        result = await log_meeting(input_data, mcp_client)

        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.created_at == result.updated_at

    @pytest.mark.asyncio
    async def test_log_meeting_persisted_to_database(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test that meeting is persisted to database."""
        from src.mosaic.repositories.meeting_repository import MeetingRepository

        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Test Meeting",
            description="Test description",
        )

        result = await log_meeting(input_data, mcp_client)

        # Verify it's in the database
        repo = MeetingRepository(test_session)
        fetched = await repo.get_by_id(result.id)

        assert fetched is not None
        # The model uses 'summary' field, not 'description'
        assert fetched.summary == "Test description"
