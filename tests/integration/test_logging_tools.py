"""Integration tests for delete_meeting tool.

Tests end-to-end meeting deletion through real MCP server,
including cascade deletion of attendees and not-found error handling.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.meeting import Meeting, MeetingAttendee
from src.mosaic.models.person import Person
from src.mosaic.repositories.meeting_repository import MeetingRepository
from src.mosaic.schemas.meeting import DeleteMeetingInput
from src.mosaic.tools.logging_tools import delete_meeting


class TestDeleteMeetingTool:
    """Test delete_meeting tool with real MCP server."""

    @pytest.mark.asyncio
    async def test_delete_meeting_success(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test successfully deleting a meeting.

        Create meeting → delete → verify deleted.
        """
        # Create a meeting
        meeting = Meeting(
            title="Team Standup",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Daily standup meeting",
        )
        test_session.add(meeting)
        await test_session.commit()
        await test_session.refresh(meeting)

        meeting_id = meeting.id

        # Delete the meeting
        input_data = DeleteMeetingInput(meeting_id=meeting_id)
        result = await delete_meeting(input_data, mcp_client)

        assert result.success is True
        assert str(meeting_id) in result.message
        assert "deleted" in result.message.lower()

        # Verify it's deleted from database
        async with mcp_client.request_context.lifespan_context.session_factory() as fresh_session:
            repo = MeetingRepository(fresh_session)
            fetched = await repo.get_by_id(meeting_id)
            assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_meeting_not_found(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test deleting a non-existent meeting raises ValueError.

        Delete non-existent meeting (should raise ValueError).
        """
        input_data = DeleteMeetingInput(meeting_id=999)

        with pytest.raises(ValueError) as exc_info:
            await delete_meeting(input_data, mcp_client)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_meeting_cascade_attendees(
        self,
        mcp_client,
        test_session: AsyncSession,
        person: Person,
    ):
        """Test that deleting a meeting also deletes attendees (CASCADE behavior).

        Create meeting with attendees → delete meeting → verify attendees also deleted.
        """
        # Create another person
        person2 = Person(full_name="Jane Smith", email="jane@example.com")
        test_session.add(person2)
        await test_session.commit()
        await test_session.refresh(person2)

        # Create meeting
        meeting = Meeting(
            title="Sprint Planning",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            summary="Planning meeting",
        )
        test_session.add(meeting)
        await test_session.commit()
        await test_session.refresh(meeting)

        # Add attendees
        attendee1 = MeetingAttendee(meeting_id=meeting.id, person_id=person.id)
        attendee2 = MeetingAttendee(meeting_id=meeting.id, person_id=person2.id)
        test_session.add_all([attendee1, attendee2])
        await test_session.commit()
        await test_session.refresh(attendee1)
        await test_session.refresh(attendee2)

        meeting_id = meeting.id
        attendee1_id = attendee1.id
        attendee2_id = attendee2.id

        # Delete the meeting
        input_data = DeleteMeetingInput(meeting_id=meeting_id)
        result = await delete_meeting(input_data, mcp_client)

        assert result.success is True

        # Verify meeting is deleted
        async with mcp_client.request_context.lifespan_context.session_factory() as fresh_session:
            repo = MeetingRepository(fresh_session)
            fetched_meeting = await repo.get_by_id(meeting_id)
            assert fetched_meeting is None

            # Verify attendees are also deleted (CASCADE)
            from sqlalchemy import select

            stmt = select(MeetingAttendee).where(
                MeetingAttendee.id.in_([attendee1_id, attendee2_id])
            )
            result = await fresh_session.execute(stmt)
            remaining_attendees = result.scalars().all()
            assert len(remaining_attendees) == 0, "Attendees should be cascaded deleted"

            # Verify persons still exist (they should NOT be deleted)
            from src.mosaic.repositories.person_repository import PersonRepository

            person_repo = PersonRepository(fresh_session)
            fetched_person1 = await person_repo.get_by_id(person.id)
            fetched_person2 = await person_repo.get_by_id(person2.id)
            assert fetched_person1 is not None, "Person should not be deleted"
            assert fetched_person2 is not None, "Person should not be deleted"
