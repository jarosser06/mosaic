"""Tests for query result schemas with discriminated unions (15 test cases)."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.mosaic.models.base import (
    ClientStatus,
    ClientType,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
    WeekBoundary,
)
from src.mosaic.schemas.query import (
    ClientResult,
    EmployerResult,
    EmploymentHistoryResult,
    MeetingResult,
    NoteResult,
    PersonResult,
    ProjectResult,
    QueryInput,
    QueryOutput,
    ReminderResult,
    UserResult,
    WorkSessionResult,
)


def test_query_input_valid():
    """Test valid QueryInput creation."""
    schema = QueryInput(query="How many hours did I work last week?")
    assert schema.query == "How many hours did I work last week?"


def test_query_input_rejects_empty_query():
    """Test that empty query is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        QueryInput(query="")
    assert "at least 1 character" in str(exc_info.value).lower()


def test_query_input_rejects_long_query():
    """Test that query exceeding max_length is rejected."""
    long_query = "x" * 2001  # Exceeds 2000 max
    with pytest.raises(ValidationError) as exc_info:
        QueryInput(query=long_query)
    assert "at most 2000 characters" in str(exc_info.value).lower()


def test_work_session_result_discriminator():
    """Test WorkSessionResult has correct discriminator."""
    work_date = date(2026, 1, 15)
    created = datetime(2026, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 9, 5, 0, tzinfo=timezone.utc)

    schema = WorkSessionResult(
        id=1,
        date=work_date,
        project_id=42,
        duration_hours=Decimal("8.0"),
        description="Work description",
        privacy_level=PrivacyLevel.PRIVATE,
        tags=["backend"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "work_session"
    assert schema.id == 1
    assert schema.date == work_date


def test_meeting_result_discriminator():
    """Test MeetingResult has correct discriminator."""
    start = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 14, 5, 0, tzinfo=timezone.utc)

    schema = MeetingResult(
        id=1,
        start_time=start,
        end_time=end,
        title="Sprint Planning",
        attendees=[1, 2, 3],
        project_id=42,
        description="Meeting notes",
        privacy_level=PrivacyLevel.PRIVATE,
        tags=["planning"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "meeting"
    assert schema.title == "Sprint Planning"


def test_person_result_discriminator():
    """Test PersonResult has correct discriminator."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = PersonResult(
        id=1,
        full_name="John Doe",
        email="john@example.com",
        phone="+1-555-123-4567",
        company="Acme Corp",
        title="Senior Engineer",
        notes="Met at conference",
        tags=["client", "technical"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "person"
    assert schema.full_name == "John Doe"


def test_client_result_discriminator():
    """Test ClientResult has correct discriminator."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = ClientResult(
        id=1,
        name="Acme Corporation",
        client_type=ClientType.COMPANY,
        status=ClientStatus.ACTIVE,
        contact_person_id=5,
        notes="Main client",
        tags=["enterprise"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "client"
    assert schema.name == "Acme Corporation"
    assert schema.client_type == ClientType.COMPANY


def test_project_result_discriminator():
    """Test ProjectResult has correct discriminator."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = ProjectResult(
        id=1,
        name="Website Redesign",
        client_id=5,
        status=ProjectStatus.ACTIVE,
        on_behalf_of=2,
        description="Redesign project",
        tags=["web", "frontend"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "project"
    assert schema.name == "Website Redesign"
    assert schema.status == ProjectStatus.ACTIVE


def test_employer_result_discriminator():
    """Test EmployerResult has correct discriminator."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = EmployerResult(
        id=1,
        name="Tech Corp",
        notes="Current employer",
        tags=["technology"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "employer"
    assert schema.name == "Tech Corp"


def test_note_result_discriminator():
    """Test NoteResult has correct discriminator."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = NoteResult(
        id=1,
        content="Remember to follow up",
        entity_type_attached=EntityType.PROJECT,
        entity_id_attached=42,
        privacy_level=PrivacyLevel.PRIVATE,
        tags=["important"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "note"
    assert schema.content == "Remember to follow up"


def test_reminder_result_discriminator():
    """Test ReminderResult has correct discriminator."""
    reminder_time = datetime(2026, 1, 20, 9, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = ReminderResult(
        id=1,
        reminder_time=reminder_time,
        message="Call client",
        entity_type_attached=EntityType.CLIENT,
        entity_id_attached=5,
        is_completed=False,
        snoozed_until=None,
        tags=["urgent"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "reminder"
    assert schema.message == "Call client"


def test_user_result_discriminator():
    """Test UserResult has correct discriminator."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = UserResult(
        id=1,
        full_name="John Doe",
        email="john.doe@example.com",
        timezone="America/New_York",
        week_boundary=WeekBoundary.MONDAY_FRIDAY,
        created_at=created,
        updated_at=updated,
    )

    assert schema.entity_type == "user"
    assert schema.email == "john.doe@example.com"
    assert schema.week_boundary == WeekBoundary.MONDAY_FRIDAY


def test_employment_history_result_discriminator():
    """Test EmploymentHistoryResult has correct discriminator."""
    start_date = date(2025, 1, 15)

    schema = EmploymentHistoryResult(
        id=1,
        person_id=5,
        employer_id=2,
        start_date=start_date,
        end_date=None,
        title="Software Engineer",
    )

    assert schema.entity_type == "employment_history"
    assert schema.person_id == 5


def test_query_output_with_discriminated_union():
    """Test QueryOutput with mixed entity types (discriminated union)."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    person = PersonResult(
        id=1,
        full_name="John Doe",
        email="john@example.com",
        phone=None,
        company=None,
        title=None,
        notes=None,
        tags=[],
        created_at=created,
        updated_at=updated,
    )

    client = ClientResult(
        id=2,
        name="Acme Corp",
        client_type=ClientType.COMPANY,
        status=ClientStatus.ACTIVE,
        contact_person_id=None,
        notes=None,
        tags=[],
        created_at=created,
        updated_at=updated,
    )

    schema = QueryOutput(
        summary="Found 2 results",
        results=[person, client],
        total_count=2,
    )

    assert schema.total_count == 2
    assert len(schema.results) == 2
    assert schema.results[0].entity_type == "person"
    assert schema.results[1].entity_type == "client"


def test_query_output_empty_results():
    """Test QueryOutput with no results."""
    schema = QueryOutput(
        summary="No results found",
        results=[],
        total_count=0,
    )

    assert schema.total_count == 0
    assert schema.results == []
