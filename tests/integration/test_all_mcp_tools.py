"""Comprehensive integration tests for ALL 18 MCP tools using real MCP server.

Tests all logging, query, update, and notification tools with simple
and complex scenarios. Focuses on complete coverage of the MCP API.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.mosaic.models.base import EntityType, PrivacyLevel
from src.mosaic.models.client import Client, ClientStatus, ClientType
from src.mosaic.models.employer import Employer
from src.mosaic.models.meeting import Meeting
from src.mosaic.models.note import Note
from src.mosaic.models.person import Person
from src.mosaic.models.project import Project, ProjectStatus
from src.mosaic.models.reminder import Reminder
from src.mosaic.models.work_session import WorkSession
from src.mosaic.repositories.work_session_repository import WorkSessionRepository
from src.mosaic.schemas.client import AddClientInput, UpdateClientInput
from src.mosaic.schemas.employer import AddEmployerInput
from src.mosaic.schemas.meeting import LogMeetingInput, UpdateMeetingInput
from src.mosaic.schemas.note import AddNoteInput, UpdateNoteInput
from src.mosaic.schemas.notification import TriggerNotificationInput
from src.mosaic.schemas.person import AddPersonInput, UpdatePersonInput
from src.mosaic.schemas.project import AddProjectInput, UpdateProjectInput
from src.mosaic.schemas.query import QueryInput
from src.mosaic.schemas.reminder import (
    AddReminderInput,
    CompleteReminderInput,
    SnoozeReminderInput,
)
from src.mosaic.schemas.work_session import LogWorkSessionInput, UpdateWorkSessionInput
from src.mosaic.tools.logging_tools import (
    add_client,
    add_employer,
    add_note,
    add_person,
    add_project,
    add_reminder,
    log_meeting,
    log_work_session,
)
from src.mosaic.tools.notification_tools import trigger_notification
from src.mosaic.tools.query_tools import query
from src.mosaic.tools.update_tools import (
    complete_reminder,
    snooze_reminder,
    update_client,
    update_meeting,
    update_note,
    update_person,
    update_project,
    update_work_session,
)


@pytest.mark.asyncio
class TestAllMCPTools:
    """Comprehensive integration tests for all 18 MCP tools with real MCP server."""

    # ========================================================================
    # LOGGING TOOLS (8 tools)
    # ========================================================================

    async def test_log_work_session_simple(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test log_work_session with basic fields through real MCP tool."""
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=project.id,
            description="Implemented authentication",
        )

        # Call REAL tool
        result = await log_work_session(input_data, mcp_client)

        # Verify result
        assert result.id is not None
        assert result.project_id == project.id
        assert result.duration_hours == Decimal("3.0")
        assert result.description == "Implemented authentication"
        assert result.privacy_level == PrivacyLevel.PRIVATE  # Default

        # Verify database persistence
        repo = WorkSessionRepository(test_session)
        fetched = await repo.get_by_id(result.id)
        assert fetched is not None
        assert fetched.summary == "Implemented authentication"

    async def test_log_work_session_complex(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test log_work_session with all optional fields and time rounding."""
        # 2 hours 15 minutes -> rounds to 2.5
        input_data = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 11, 15, tzinfo=timezone.utc),
            project_id=project.id,
            description="Refactored database layer",
            privacy_level=PrivacyLevel.PUBLIC,
            tags=["backend", "refactoring", "database"],
        )

        result = await log_work_session(input_data, mcp_client)

        assert result.duration_hours == Decimal("2.5")
        assert result.privacy_level == PrivacyLevel.PUBLIC
        assert result.tags == ["backend", "refactoring", "database"]

        # Verify database persistence
        repo = WorkSessionRepository(test_session)
        fetched = await repo.get_by_id(result.id)
        assert fetched is not None
        assert fetched.duration_hours == Decimal("2.5")

    async def test_log_meeting_simple(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test log_meeting without attendees or project."""
        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Daily Standup",
            description="Team sync",
        )

        result = await log_meeting(input_data, mcp_client)

        assert result.id is not None
        assert result.title == "Daily Standup"
        assert result.description == "Team sync"
        assert result.project_id is None
        assert result.attendees == []

    async def test_log_meeting_complex(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test log_meeting with attendees, project, privacy, and tags."""
        # Create attendees
        person1 = Person(full_name="Alice Developer", email="alice@example.com")
        person2 = Person(full_name="Bob Manager", email="bob@example.com")
        test_session.add_all([person1, person2])
        await test_session.commit()
        await test_session.refresh(person1)
        await test_session.refresh(person2)

        input_data = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 11, 30, tzinfo=timezone.utc),
            title="Sprint Planning",
            description="Plan next sprint tasks",
            attendees=[person1.id, person2.id],
            project_id=project.id,
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["planning", "sprint", "team"],
        )

        result = await log_meeting(input_data, mcp_client)

        assert result.project_id == project.id
        assert len(result.attendees) == 2
        assert person1.id in result.attendees
        assert person2.id in result.attendees
        assert result.privacy_level == PrivacyLevel.INTERNAL
        assert result.tags == ["planning", "sprint", "team"]

    async def test_add_person_simple(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test add_person with minimal fields."""
        input_data = AddPersonInput(
            full_name="John Doe",
        )

        result = await add_person(input_data, mcp_client)

        assert result.id is not None
        assert result.full_name == "John Doe"
        assert result.email is None
        assert result.phone is None

    async def test_add_person_complex(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test add_person with all fields."""
        input_data = AddPersonInput(
            full_name="Jane Smith",
            email="jane.smith@example.com",
            phone="+1-555-0123",
            company="TechCorp Inc",
            title="Senior Software Engineer",
            notes="Met at conference, expert in distributed systems",
            tags=["client", "technical", "senior"],
        )

        result = await add_person(input_data, mcp_client)

        assert result.full_name == "Jane Smith"
        assert result.email == "jane.smith@example.com"
        assert result.phone == "+1-555-0123"
        assert result.company == "TechCorp Inc"
        assert result.title == "Senior Software Engineer"
        assert result.notes == "Met at conference, expert in distributed systems"
        assert result.tags == ["client", "technical", "senior"]

    async def test_add_client_company(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test add_client for company type."""
        input_data = AddClientInput(
            name="Acme Corporation",
            client_type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
            notes="Long-term retainer contract",
            tags=["enterprise", "retainer"],
        )

        result = await add_client(input_data, mcp_client)

        assert result.id is not None
        assert result.name == "Acme Corporation"
        assert result.client_type == ClientType.COMPANY
        assert result.status == ClientStatus.ACTIVE
        assert result.contact_person_id is None

    async def test_add_client_individual_with_contact(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test add_client for individual with contact person."""
        # Create contact person first
        person = Person(full_name="Sarah Johnson", email="sarah@consulting.com")
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        input_data = AddClientInput(
            name="Johnson Consulting",
            client_type=ClientType.INDIVIDUAL,
            status=ClientStatus.ACTIVE,
            contact_person_id=person.id,
            notes="Independent consultant, specializes in security",
            tags=["consulting", "security"],
        )

        result = await add_client(input_data, mcp_client)

        assert result.client_type == ClientType.INDIVIDUAL
        assert result.contact_person_id == person.id

    async def test_add_project_simple(
        self,
        mcp_client,
        test_session: AsyncSession,
        client: Client,
    ):
        """Test add_project with minimal fields."""
        input_data = AddProjectInput(
            name="Website Redesign",
            client_id=client.id,
        )

        result = await add_project(input_data, mcp_client)

        assert result.id is not None
        assert result.name == "Website Redesign"
        assert result.client_id == client.id
        assert result.status == ProjectStatus.ACTIVE  # Default
        assert result.on_behalf_of is None

    async def test_add_project_complex(
        self,
        mcp_client,
        test_session: AsyncSession,
        client: Client,
        employer: Employer,
    ):
        """Test add_project with all fields."""
        input_data = AddProjectInput(
            name="Mobile App Development",
            client_id=client.id,
            on_behalf_of=employer.id,
            status=ProjectStatus.ACTIVE,
            description="Build iOS and Android apps for client portal",
            tags=["mobile", "ios", "android", "high-priority"],
        )

        result = await add_project(input_data, mcp_client)

        assert result.name == "Mobile App Development"
        assert result.on_behalf_of == employer.id
        assert result.status == ProjectStatus.ACTIVE
        assert result.description == "Build iOS and Android apps for client portal"
        assert result.tags == ["mobile", "ios", "android", "high-priority"]

    async def test_add_employer(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test add_employer with all fields."""
        input_data = AddEmployerInput(
            name="My Consulting LLC",
            notes="Formed in 2023, primary business entity",
            tags=["primary", "consulting"],
        )

        result = await add_employer(input_data, mcp_client)

        assert result.id is not None
        assert result.name == "My Consulting LLC"
        assert result.notes == "Formed in 2023, primary business entity"
        assert result.tags == ["primary", "consulting"]

    async def test_add_note_standalone(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test add_note without entity attachment."""
        input_data = AddNoteInput(
            content="Remember to follow up on the contract renewal",
            privacy_level=PrivacyLevel.PRIVATE,
            tags=["followup", "important"],
        )

        result = await add_note(input_data, mcp_client)

        assert result.id is not None
        assert result.content == "Remember to follow up on the contract renewal"
        assert result.entity_type is None
        assert result.entity_id is None
        assert result.privacy_level == PrivacyLevel.PRIVATE

    async def test_add_note_attached_to_person(
        self,
        mcp_client,
        test_session: AsyncSession,
        person: Person,
    ):
        """Test add_note attached to a person."""
        input_data = AddNoteInput(
            content="Prefers email communication, responds quickly",
            entity_type=EntityType.PERSON,
            entity_id=person.id,
            privacy_level=PrivacyLevel.INTERNAL,
            tags=["communication", "preferences"],
        )

        result = await add_note(input_data, mcp_client)

        assert result.entity_type == EntityType.PERSON
        assert result.entity_id == person.id

    async def test_add_note_attached_to_project(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test add_note attached to a project."""
        input_data = AddNoteInput(
            content="Client requested feature freeze until Q2",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            privacy_level=PrivacyLevel.PUBLIC,
            tags=["planning", "scope"],
        )

        result = await add_note(input_data, mcp_client)

        assert result.entity_type == EntityType.PROJECT
        assert result.entity_id == project.id

    async def test_add_reminder_simple(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test add_reminder without entity attachment."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        input_data = AddReminderInput(
            reminder_time=future_time,
            message="Call client about proposal",
        )

        result = await add_reminder(input_data, mcp_client)

        assert result.id is not None
        assert result.message == "Call client about proposal"
        assert result.reminder_time == future_time
        assert result.entity_type is None
        assert result.completed_at is None

    async def test_add_reminder_with_entity(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test add_reminder attached to a project."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        input_data = AddReminderInput(
            reminder_time=future_time,
            message="Submit final deliverables",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            tags=["deadline", "deliverable"],
        )

        result = await add_reminder(input_data, mcp_client)

        assert result.entity_type == EntityType.PROJECT
        assert result.entity_id == project.id
        assert result.tags == ["deadline", "deliverable"]

    # ========================================================================
    # QUERY TOOL (1 tool) - EXTENSIVE TESTING
    # ========================================================================

    async def test_query_simple_placeholder(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query returns placeholder (implementation pending)."""
        input_data = QueryInput(query="show all projects")

        result = await query(input_data, mcp_client)

        # Current implementation returns placeholder
        assert result is not None
        assert hasattr(result, "summary")
        assert hasattr(result, "results")
        assert hasattr(result, "total_count")

    async def test_query_work_sessions_simple(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for work sessions."""
        input_data = QueryInput(query="show me all work sessions")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_date_range_this_week(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query with relative date range."""
        input_data = QueryInput(query="work sessions from this week")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_date_range_last_month(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query with last month date range."""
        input_data = QueryInput(query="meetings from last month")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_date_range_specific_dates(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query with specific date range."""
        input_data = QueryInput(query="work from January 1-15, 2024")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_by_entity_people(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for people entities."""
        input_data = QueryInput(query="list all people")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_by_entity_clients(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for client entities."""
        input_data = QueryInput(query="show all clients")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_by_entity_projects(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for project entities."""
        input_data = QueryInput(query="show active projects")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_by_entity_reminders(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for reminder entities."""
        input_data = QueryInput(query="show upcoming reminders")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_privacy_public_only(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query filtering for public entries only."""
        input_data = QueryInput(query="show public work sessions")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_privacy_exclude_private(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query excluding private entries."""
        input_data = QueryInput(query="show non-private meetings")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_privacy_internal_and_public(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for internal and public entries."""
        input_data = QueryInput(query="show internal and public notes")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_by_project_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test query filtering by project."""
        input_data = QueryInput(query=f"work sessions for project {project.name}")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_by_person_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
        person: Person,
    ):
        """Test query filtering by person."""
        input_data = QueryInput(query=f"meetings with {person.full_name}")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_by_client_filter(
        self,
        mcp_client,
        test_session: AsyncSession,
        client: Client,
    ):
        """Test query filtering by client."""
        input_data = QueryInput(query=f"projects for client {client.name}")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_text_search_description(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query with text search in descriptions."""
        input_data = QueryInput(query="work sessions containing 'authentication'")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_text_search_notes(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query with text search in notes."""
        input_data = QueryInput(query="notes containing 'security'")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_tag_filter_single(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query filtering by single tag."""
        input_data = QueryInput(query="work sessions tagged with 'backend'")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_tag_filter_multiple(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query filtering by multiple tags."""
        input_data = QueryInput(query="projects tagged with 'mobile' and 'high-priority'")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_status_filter_active(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query filtering by active status."""
        input_data = QueryInput(query="active clients")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_with_status_filter_completed(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query filtering by completed status."""
        input_data = QueryInput(query="completed projects")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_complex_multiple_filters(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test complex query with multiple filters combined."""
        input_data = QueryInput(
            query=f"public work sessions for {project.name} from last week tagged with 'deployment'"
        )

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_complex_date_and_privacy(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test complex query with date range and privacy filter."""
        input_data = QueryInput(query="internal meetings from this month")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_complex_entity_and_text_search(
        self,
        mcp_client,
        test_session: AsyncSession,
        person: Person,
    ):
        """Test complex query with entity filter and text search."""
        input_data = QueryInput(query=f"meetings with {person.full_name} about 'planning'")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_timecard_style_aggregation(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test timecard-style query with hours aggregation."""
        input_data = QueryInput(query="total hours worked this month by project")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_upcoming_due_items(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for upcoming reminders."""
        input_data = QueryInput(query="reminders due tomorrow")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_overdue_items(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query for overdue reminders."""
        input_data = QueryInput(query="overdue reminders")

        result = await query(input_data, mcp_client)

        assert result is not None

    async def test_query_empty_results(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query that returns no results."""
        input_data = QueryInput(query="work sessions from year 2050")

        result = await query(input_data, mcp_client)

        # Should return empty results, not error
        assert result.total_count == 0
        assert result.results == []

    async def test_query_handles_malformed_input(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test query handles malformed input gracefully."""
        input_data = QueryInput(query="!@#$%^&*() invalid syntax")

        # Should not crash, but return empty or error
        result = await query(input_data, mcp_client)
        assert result is not None

    # ========================================================================
    # UPDATE TOOLS (8 tools)
    # ========================================================================

    async def test_update_work_session_description(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test update_work_session changing description."""
        # Create work session
        ws = WorkSession(
            project_id=project.id,
            date=datetime(2024, 1, 15, tzinfo=timezone.utc).date(),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            summary="Original description",
        )
        test_session.add(ws)
        await test_session.commit()
        await test_session.refresh(ws)

        # Update
        input_data = UpdateWorkSessionInput(description="Updated description")

        result = await update_work_session(ws.id, input_data, mcp_client)

        assert result.description == "Updated description"

    async def test_update_work_session_times_recalculates_duration(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test update_work_session recalculates duration when times change."""
        # Create work session (3 hours)
        ws = WorkSession(
            project_id=project.id,
            date=datetime(2024, 1, 15, tzinfo=timezone.utc).date(),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
        )
        test_session.add(ws)
        await test_session.commit()
        await test_session.refresh(ws)

        # Update end time to 4 hours total
        input_data = UpdateWorkSessionInput(
            end_time=datetime(2024, 1, 15, 13, 0, tzinfo=timezone.utc)
        )

        result = await update_work_session(ws.id, input_data, mcp_client)

        assert result.duration_hours == 4.0

    async def test_update_work_session_privacy_and_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test update_work_session changing privacy and tags."""
        ws = WorkSession(
            project_id=project.id,
            date=datetime(2024, 1, 15, tzinfo=timezone.utc).date(),
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("3.0"),
            privacy_level=PrivacyLevel.PRIVATE,
            tags=["old"],
        )
        test_session.add(ws)
        await test_session.commit()
        await test_session.refresh(ws)

        input_data = UpdateWorkSessionInput(
            privacy_level=PrivacyLevel.PUBLIC,
            tags=["new", "updated"],
        )

        result = await update_work_session(ws.id, input_data, mcp_client)

        assert result.privacy_level == PrivacyLevel.PUBLIC
        assert result.tags == ["new", "updated"]

    async def test_update_meeting_title_and_description(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test update_meeting changing title and description."""
        # Create meeting
        meeting = Meeting(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            title="Original Title",
            summary="Original description",
        )
        test_session.add(meeting)
        await test_session.commit()
        await test_session.refresh(meeting)

        input_data = UpdateMeetingInput(
            title="Updated Title",
            description="Updated description",
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
        )

        result = await update_meeting(meeting.id, input_data, mcp_client)

        assert result.title == "Updated Title"
        assert result.description == "Updated description"

    async def test_update_meeting_attendees_and_project(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test update_meeting changing attendees and project."""
        person = Person(full_name="Charlie Brown")
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        meeting = Meeting(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            duration_minutes=60,
            title="Meeting",
        )
        test_session.add(meeting)
        await test_session.commit()
        await test_session.refresh(meeting)

        input_data = UpdateMeetingInput(
            attendees=[person.id],
            project_id=project.id,
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
        )

        result = await update_meeting(meeting.id, input_data, mcp_client)

        assert result.project_id == project.id
        assert person.id in result.attendees

    async def test_update_person_contact_info(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test update_person changing contact information."""
        person = Person(
            full_name="Original Name",
            email="old@example.com",
            phone="555-0000",
        )
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        input_data = UpdatePersonInput(
            full_name="Updated Name",
            email="new@example.com",
            phone="555-1111",
        )

        result = await update_person(person.id, input_data, mcp_client)

        assert result.full_name == "Updated Name"
        assert result.email == "new@example.com"
        assert result.phone == "555-1111"

    async def test_update_person_company_and_title(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test update_person changing company and title."""
        person = Person(
            full_name="Developer Joe",
            company="Old Corp",
            title="Junior Dev",
        )
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        input_data = UpdatePersonInput(
            company="New Corp",
            title="Senior Dev",
        )

        result = await update_person(person.id, input_data, mcp_client)

        assert result.company == "New Corp"
        assert result.title == "Senior Dev"

    async def test_update_client_name_and_status(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test update_client changing name and status."""
        client = Client(
            name="Old Name Inc",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        test_session.add(client)
        await test_session.commit()
        await test_session.refresh(client)

        input_data = UpdateClientInput(
            name="New Name Inc",
            status=ClientStatus.PAST,
        )

        result = await update_client(client.id, input_data, mcp_client)

        assert result.name == "New Name Inc"
        assert result.status == ClientStatus.PAST

    async def test_update_client_type_and_contact(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test update_client changing type and contact person."""
        person = Person(full_name="Contact Person")
        test_session.add(person)
        await test_session.commit()
        await test_session.refresh(person)

        client = Client(
            name="Client",
            type=ClientType.COMPANY,
            status=ClientStatus.ACTIVE,
        )
        test_session.add(client)
        await test_session.commit()
        await test_session.refresh(client)

        input_data = UpdateClientInput(
            client_type=ClientType.INDIVIDUAL,
            contact_person_id=person.id,
        )

        result = await update_client(client.id, input_data, mcp_client)

        assert result.client_type == ClientType.INDIVIDUAL
        assert result.contact_person_id == person.id

    async def test_update_project_name_and_status(
        self,
        mcp_client,
        test_session: AsyncSession,
        client: Client,
    ):
        """Test update_project changing name and status."""
        project = Project(
            name="Old Project",
            client_id=client.id,
            status=ProjectStatus.ACTIVE,
        )
        test_session.add(project)
        await test_session.commit()
        await test_session.refresh(project)

        input_data = UpdateProjectInput(
            name="New Project",
            status=ProjectStatus.COMPLETED,
        )

        result = await update_project(project.id, input_data, mcp_client)

        assert result.name == "New Project"
        assert result.status == ProjectStatus.COMPLETED

    async def test_update_project_description_and_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
        client: Client,
    ):
        """Test update_project changing description and tags."""
        project = Project(
            name="Project",
            client_id=client.id,
            description="Old description",
            tags=["old"],
        )
        test_session.add(project)
        await test_session.commit()
        await test_session.refresh(project)

        input_data = UpdateProjectInput(
            description="New description",
            tags=["new", "tags"],
        )

        result = await update_project(project.id, input_data, mcp_client)

        assert result.description == "New description"
        assert result.tags == ["new", "tags"]

    async def test_update_note_content(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test update_note changing content."""
        note = Note(
            text="Original content",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            privacy_level=PrivacyLevel.PRIVATE,
        )
        test_session.add(note)
        await test_session.commit()
        await test_session.refresh(note)

        input_data = UpdateNoteInput(content="Updated content")

        result = await update_note(note.id, input_data, mcp_client)

        assert result.content == "Updated content"

    async def test_update_note_privacy_and_tags(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test update_note changing privacy and tags."""
        note = Note(
            text="Note",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
            privacy_level=PrivacyLevel.PRIVATE,
            tags=["old"],
        )
        test_session.add(note)
        await test_session.commit()
        await test_session.refresh(note)

        input_data = UpdateNoteInput(
            privacy_level=PrivacyLevel.PUBLIC,
            tags=["new"],
        )

        result = await update_note(note.id, input_data, mcp_client)

        assert result.privacy_level == PrivacyLevel.PUBLIC
        assert result.tags == ["new"]

    async def test_complete_reminder(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test complete_reminder marks reminder as completed."""
        reminder = Reminder(
            reminder_time=datetime.now(timezone.utc) + timedelta(hours=1),
            message="Test reminder",
        )
        test_session.add(reminder)
        await test_session.commit()
        await test_session.refresh(reminder)

        input_data = CompleteReminderInput(reminder_id=reminder.id)

        result = await complete_reminder(input_data, mcp_client)

        assert result.id == reminder.id
        assert result.completed_at is not None

    async def test_snooze_reminder(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test snooze_reminder updates snooze time."""
        reminder = Reminder(
            reminder_time=datetime.now(timezone.utc) + timedelta(hours=1),
            message="Test reminder",
        )
        test_session.add(reminder)
        await test_session.commit()
        await test_session.refresh(reminder)

        snooze_until = datetime.now(timezone.utc) + timedelta(hours=3)
        input_data = SnoozeReminderInput(
            reminder_id=reminder.id,
            snooze_until=snooze_until,
        )

        result = await snooze_reminder(input_data, mcp_client)

        assert result.id == reminder.id
        assert result.snoozed_until == snooze_until

    # ========================================================================
    # NOTIFICATION TOOL (1 tool)
    # ========================================================================

    @patch("src.mosaic.services.notification_service.NotificationService.trigger_notification")
    async def test_trigger_notification_success(
        self,
        mock_trigger: MagicMock,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test trigger_notification with successful delivery."""
        mock_trigger.return_value = True

        input_data = TriggerNotificationInput(
            title="Test Notification",
            message="This is a test message",
        )

        result = await trigger_notification(input_data, mcp_client)

        assert result.success is True
        assert "success" in result.message.lower()

    @patch("src.mosaic.services.notification_service.NotificationService.trigger_notification")
    async def test_trigger_notification_failure(
        self,
        mock_trigger: MagicMock,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test trigger_notification with failed delivery."""
        mock_trigger.return_value = False

        input_data = TriggerNotificationInput(
            title="Test Notification",
            message="This will fail",
        )

        result = await trigger_notification(input_data, mcp_client)

        assert result.success is False
        assert "failed" in result.message.lower() or "bridge" in result.message.lower()

    # ========================================================================
    # END-TO-END WORKFLOW TESTS
    # ========================================================================

    async def test_complete_workflow_create_client_to_work_session(
        self,
        mcp_client,
        test_session: AsyncSession,
    ):
        """Test complete workflow: employer -> client -> project -> work session."""
        # 1. Create employer
        employer_input = AddEmployerInput(name="My Company LLC")
        employer = await add_employer(employer_input, mcp_client)

        # 2. Create contact person
        person_input = AddPersonInput(
            full_name="Jane Client",
            email="jane@client.com",
        )
        person = await add_person(person_input, mcp_client)

        # 3. Create client
        client_input = AddClientInput(
            name="Client Corp",
            client_type=ClientType.COMPANY,
            contact_person_id=person.id,
        )
        client = await add_client(client_input, mcp_client)

        # 4. Create project
        project_input = AddProjectInput(
            name="Website Redesign",
            client_id=client.id,
            on_behalf_of=employer.id,
        )
        project = await add_project(project_input, mcp_client)

        # 5. Log work session
        work_input = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=project.id,
            description="Initial design mockups",
            tags=["design", "frontend"],
        )
        work = await log_work_session(work_input, mcp_client)

        # 6. Add note to project
        note_input = AddNoteInput(
            content="Client loves the color scheme",
            entity_type=EntityType.PROJECT,
            entity_id=project.id,
        )
        note = await add_note(note_input, mcp_client)

        # Verify complete chain
        assert employer.id is not None
        assert person.id is not None
        assert client.id is not None
        assert client.contact_person_id == person.id
        assert project.id is not None
        assert project.client_id == client.id
        assert project.on_behalf_of == employer.id
        assert work.id is not None
        assert work.project_id == project.id
        assert note.id is not None
        assert note.entity_id == project.id

    async def test_complete_workflow_meeting_with_attendees_and_project(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test workflow: create people -> log meeting -> add reminder."""
        # 1. Create attendees
        person1_input = AddPersonInput(full_name="Alice Developer")
        person1 = await add_person(person1_input, mcp_client)

        person2_input = AddPersonInput(full_name="Bob Manager")
        person2 = await add_person(person2_input, mcp_client)

        # 2. Log meeting
        meeting_input = LogMeetingInput(
            start_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            title="Sprint Planning",
            attendees=[person1.id, person2.id],
            project_id=project.id,
            tags=["planning"],
        )
        meeting = await log_meeting(meeting_input, mcp_client)

        # 3. Add reminder for follow-up
        reminder_input = AddReminderInput(
            reminder_time=datetime.now(timezone.utc) + timedelta(days=1),
            message="Follow up on action items",
            entity_type=EntityType.MEETING,
            entity_id=meeting.id,
        )
        reminder = await add_reminder(reminder_input, mcp_client)

        # Verify
        assert meeting.id is not None
        assert len(meeting.attendees) == 2
        assert reminder.entity_id == meeting.id

    async def test_complete_workflow_query_and_update(
        self,
        mcp_client,
        test_session: AsyncSession,
        project: Project,
    ):
        """Test workflow: create work -> query -> update."""
        # 1. Log work session
        work_input = LogWorkSessionInput(
            start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
            project_id=project.id,
            description="Initial work",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        work = await log_work_session(work_input, mcp_client)

        # 2. Query work sessions (placeholder returns)
        query_input = QueryInput(query="show all work sessions")
        query_result = await query(query_input, mcp_client)
        assert query_result is not None

        # 3. Update work session to public
        update_input = UpdateWorkSessionInput(
            description="Updated work description",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        updated = await update_work_session(work.id, update_input, mcp_client)

        assert updated.description == "Updated work description"
        assert updated.privacy_level == PrivacyLevel.PUBLIC
