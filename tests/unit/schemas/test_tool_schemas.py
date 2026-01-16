"""Tests for MCP tool input/output schemas (20 test cases)."""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from src.mosaic.models.base import (
    ClientStatus,
    ClientType,
    EntityType,
    PrivacyLevel,
    ProjectStatus,
)
from src.mosaic.schemas.client import AddClientInput
from src.mosaic.schemas.employer import AddEmployerInput, AddEmployerOutput
from src.mosaic.schemas.note import AddNoteInput
from src.mosaic.schemas.person import (
    AddPersonInput,
    EmploymentHistoryInput,
    EmploymentHistoryOutput,
)
from src.mosaic.schemas.project import AddProjectInput
from src.mosaic.schemas.user import UpdateUserInput, UpdateUserOutput


# Person schemas tests
def test_add_person_input_valid():
    """Test valid AddPersonInput creation."""
    schema = AddPersonInput(
        full_name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-123-4567",
        company="Acme Corp",
        title="Senior Engineer",
        notes="Met at conference",
        tags=["client", "technical"],
    )

    assert schema.full_name == "John Doe"
    assert schema.email == "john.doe@example.com"
    assert schema.phone == "+1-555-123-4567"
    assert schema.company == "Acme Corp"
    assert schema.title == "Senior Engineer"


def test_add_person_input_email_validation():
    """Test that invalid email is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        AddPersonInput(
            full_name="John Doe",
            email="invalid-email",
        )
    assert "value is not a valid email address" in str(exc_info.value).lower()


def test_add_person_input_name_required():
    """Test that full_name is required and cannot be empty."""
    with pytest.raises(ValidationError) as exc_info:
        AddPersonInput(full_name="")
    assert "at least 1 character" in str(exc_info.value).lower()


def test_employment_history_input_validates_date_range():
    """Test EmploymentHistoryInput validates end_date >= start_date."""
    start = date(2026, 1, 31)
    end = date(2026, 1, 1)

    with pytest.raises(ValidationError) as exc_info:
        EmploymentHistoryInput(
            person_id=1,
            employer_id=2,
            start_date=start,
            end_date=end,
        )
    assert "end_date must be on or after start_date" in str(exc_info.value)


# Client schemas tests
def test_add_client_input_valid():
    """Test valid AddClientInput creation."""
    schema = AddClientInput(
        name="Acme Corporation",
        client_type=ClientType.COMPANY,
        status=ClientStatus.ACTIVE,
        contact_person_id=5,
        notes="Key account",
        tags=["enterprise"],
    )

    assert schema.name == "Acme Corporation"
    assert schema.client_type == ClientType.COMPANY
    assert schema.status == ClientStatus.ACTIVE


def test_add_client_input_status_default():
    """Test that status defaults to ACTIVE."""
    schema = AddClientInput(
        name="Acme Corp",
        client_type=ClientType.COMPANY,
    )

    assert schema.status == ClientStatus.ACTIVE


def test_add_client_input_client_type_required():
    """Test that client_type is required."""
    with pytest.raises(ValidationError) as exc_info:
        AddClientInput(name="Acme Corp")
    assert "field required" in str(exc_info.value).lower()


# Employer schemas tests
def test_add_employer_input_valid():
    """Test valid AddEmployerInput creation."""
    schema = AddEmployerInput(
        name="Tech Corp",
        notes="Parent company",
        tags=["technology", "remote"],
    )

    assert schema.name == "Tech Corp"
    assert schema.notes == "Parent company"
    assert schema.tags == ["technology", "remote"]


def test_add_employer_output_valid():
    """Test valid AddEmployerOutput creation."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = AddEmployerOutput(
        id=1,
        name="Tech Corp",
        notes="Notes",
        tags=["tech"],
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.name == "Tech Corp"


# Project schemas tests
def test_add_project_input_valid():
    """Test valid AddProjectInput creation."""
    schema = AddProjectInput(
        name="Website Redesign",
        client_id=5,
        status=ProjectStatus.ACTIVE,
        on_behalf_of=2,
        description="Complete redesign",
        tags=["web", "frontend"],
    )

    assert schema.name == "Website Redesign"
    assert schema.client_id == 5
    assert schema.status == ProjectStatus.ACTIVE
    assert schema.on_behalf_of == 2


def test_add_project_input_status_default():
    """Test that status defaults to ACTIVE."""
    schema = AddProjectInput(
        name="Project",
        client_id=1,
    )

    assert schema.status == ProjectStatus.ACTIVE


def test_add_project_input_client_id_required():
    """Test that client_id is required and must be > 0."""
    with pytest.raises(ValidationError) as exc_info:
        AddProjectInput(name="Project", client_id=0)
    assert "greater than 0" in str(exc_info.value).lower()


# Note schemas tests
def test_add_note_input_valid():
    """Test valid AddNoteInput creation."""
    schema = AddNoteInput(
        content="Remember to follow up",
        entity_type=EntityType.PROJECT,
        entity_id=42,
        privacy_level=PrivacyLevel.PRIVATE,
        tags=["important"],
    )

    assert schema.content == "Remember to follow up"
    assert schema.entity_type == EntityType.PROJECT
    assert schema.entity_id == 42
    assert schema.privacy_level == PrivacyLevel.PRIVATE


def test_add_note_input_privacy_default():
    """Test that privacy_level defaults to PRIVATE."""
    schema = AddNoteInput(content="Note content")
    assert schema.privacy_level == PrivacyLevel.PRIVATE


def test_add_note_input_content_min_length():
    """Test that empty content is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        AddNoteInput(content="")
    assert "at least 1 character" in str(exc_info.value).lower()


def test_add_note_input_content_max_length():
    """Test that content exceeding max_length is rejected."""
    long_content = "x" * 10001  # Exceeds 10000 max

    with pytest.raises(ValidationError) as exc_info:
        AddNoteInput(content=long_content)
    assert "at most 10000 characters" in str(exc_info.value).lower()


# User schemas tests
def test_update_user_profile_input_valid():
    """Test valid UpdateUserInput creation."""
    schema = UpdateUserInput(
        full_name="John Doe",
        email="john.doe@example.com",
        timezone="America/New_York",
        week_boundary="monday_friday",
    )

    assert schema.full_name == "John Doe"
    assert schema.email == "john.doe@example.com"
    assert schema.timezone == "America/New_York"
    assert schema.week_boundary == "monday_friday"


def test_update_user_profile_input_email_validation():
    """Test that invalid email is rejected in user profile."""
    with pytest.raises(ValidationError) as exc_info:
        UpdateUserInput(email="not-an-email")
    assert "value is not a valid email address" in str(exc_info.value).lower()


def test_update_user_profile_output_valid():
    """Test valid UpdateUserOutput creation."""
    created = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    updated = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    schema = UpdateUserOutput(
        id=1,
        full_name="John Doe",
        email="john.doe@example.com",
        timezone="America/New_York",
        week_boundary="monday_friday",
        created_at=created,
        updated_at=updated,
    )

    assert schema.id == 1
    assert schema.week_boundary == "monday_friday"


def test_employment_history_output_valid():
    """Test valid EmploymentHistoryOutput creation."""
    start_date = date(2025, 1, 15)

    schema = EmploymentHistoryOutput(
        id=1,
        person_id=5,
        employer_id=2,
        start_date=start_date,
        end_date=None,
        title="Software Engineer",
    )

    assert schema.id == 1
    assert schema.person_id == 5
    assert schema.employer_id == 2
    assert schema.end_date is None
