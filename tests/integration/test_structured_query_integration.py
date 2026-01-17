"""Integration tests for structured query system."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from src.mosaic.models import Client, Employer, Meeting, Person, Project, WorkSession
from src.mosaic.models.base import ClientStatus, ClientType, EntityType, PrivacyLevel, ProjectStatus
from src.mosaic.schemas.query_structured import (
    AggregationFunction,
    AggregationSpec,
    FilterOperator,
    FilterSpec,
)
from src.mosaic.services.query_service import QueryService


@pytest.mark.asyncio
async def test_simple_filter_by_date(test_session):
    """Test simple date filter on work session."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    project = Project(
        name="Test Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.flush()

    ws = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("8.0"),
        summary="Test work",
        privacy_level=PrivacyLevel.PUBLIC,
    )
    test_session.add(ws)
    await test_session.commit()

    # Execute structured query
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.WORK_SESSION,
        filters=[FilterSpec(field="date", operator=FilterOperator.GTE, value=date(2024, 1, 1))],
    )

    assert result["entity_type"] == "work_session"
    assert result["total_count"] >= 1
    assert len(result["results"]) >= 1
    assert result["results"][0].date == date(2024, 1, 15)


@pytest.mark.asyncio
async def test_relationship_filter_project_name(test_session):
    """Test filtering with relationship traversal (project.name)."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    project = Project(
        name="Enterprise Portal Redesign",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.flush()

    ws = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("8.0"),
        summary="Portal work",
        privacy_level=PrivacyLevel.PUBLIC,
    )
    test_session.add(ws)
    await test_session.commit()

    # Execute structured query with relationship filter
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.WORK_SESSION,
        filters=[
            FilterSpec(
                field="project.name",
                operator=FilterOperator.CONTAINS,
                value="Enterprise",
            )
        ],
    )

    assert result["entity_type"] == "work_session"
    assert result["total_count"] >= 1
    assert len(result["results"]) >= 1
    assert result["results"][0].description == "Portal work"


@pytest.mark.asyncio
async def test_aggregation_sum_hours(test_session):
    """Test SUM aggregation on duration_hours."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    project = Project(
        name="Test Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.flush()

    # Create 3 work sessions
    for i in range(3):
        ws = WorkSession(
            project_id=project.id,
            date=date(2024, 1, 15 + i),
            start_time=datetime(2024, 1, 15 + i, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15 + i, 17, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("8.0"),
            summary=f"Work {i}",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add(ws)
    await test_session.commit()

    # Execute aggregation query
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.WORK_SESSION,
        filters=[],
        aggregation=AggregationSpec(
            function=AggregationFunction.SUM,
            field="duration_hours",
        ),
    )

    assert result["entity_type"] == "work_session"
    assert "aggregation" in result
    assert result["aggregation"]["function"] == "sum"
    assert result["aggregation"]["field"] == "duration_hours"
    assert result["aggregation"]["result"] == Decimal("24.0")


@pytest.mark.asyncio
async def test_multiple_filters_combined(test_session):
    """Test multiple filters combined with AND logic."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    project = Project(
        name="Test Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.flush()

    # Create work sessions with different durations
    ws1 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("8.0"),
        summary="Long work",
        privacy_level=PrivacyLevel.PUBLIC,
    )
    ws2 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("2.0"),
        summary="Short work",
        privacy_level=PrivacyLevel.PRIVATE,
    )
    test_session.add_all([ws1, ws2])
    await test_session.commit()

    # Execute query with multiple filters
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.WORK_SESSION,
        filters=[
            FilterSpec(field="date", operator=FilterOperator.EQ, value=date(2024, 1, 15)),
            FilterSpec(field="duration_hours", operator=FilterOperator.GT, value=Decimal("5.0")),
        ],
    )

    assert result["entity_type"] == "work_session"
    assert result["total_count"] == 1
    assert result["results"][0].description == "Long work"


@pytest.mark.asyncio
async def test_meeting_attendees_person_name(test_session):
    """Test multi-level relationship: meeting -> attendees -> person -> full_name."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    project = Project(
        name="Test Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.flush()

    person = Person(full_name="Sarah Johnson", email="sarah@example.com")
    test_session.add(person)
    await test_session.flush()

    meeting = Meeting(
        title="Team Sync",
        summary="Weekly team meeting",
        start_time=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        duration_minutes=60,
        project_id=project.id,
        privacy_level=PrivacyLevel.PUBLIC,
    )
    test_session.add(meeting)
    await test_session.flush()

    from src.mosaic.models.meeting import MeetingAttendee

    attendee = MeetingAttendee(meeting_id=meeting.id, person_id=person.id)
    test_session.add(attendee)
    await test_session.commit()

    # Execute structured query with multi-level relationship filter
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.MEETING,
        filters=[
            FilterSpec(
                field="attendees.person.full_name",
                operator=FilterOperator.CONTAINS,
                value="Sarah",
            )
        ],
    )

    assert result["entity_type"] == "meeting"
    assert result["total_count"] >= 1


@pytest.mark.asyncio
async def test_group_by_relationship_path(test_session):
    """Test GROUP BY with relationship path (project.name)."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    # Create two projects
    project1 = Project(
        name="Project Alpha",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    project2 = Project(
        name="Project Beta",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add_all([project1, project2])
    await test_session.flush()

    # Create work sessions for both projects
    # Project Alpha: 3 sessions of 8 hours each = 24 hours
    for i in range(3):
        ws = WorkSession(
            project_id=project1.id,
            date=date(2024, 1, 15 + i),
            start_time=datetime(2024, 1, 15 + i, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 15 + i, 17, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("8.0"),
            summary=f"Alpha work {i}",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add(ws)

    # Project Beta: 2 sessions of 5 hours each = 10 hours
    for i in range(2):
        ws = WorkSession(
            project_id=project2.id,
            date=date(2024, 1, 18 + i),
            start_time=datetime(2024, 1, 18 + i, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 18 + i, 14, 0, tzinfo=timezone.utc),
            duration_hours=Decimal("5.0"),
            summary=f"Beta work {i}",
            privacy_level=PrivacyLevel.PUBLIC,
        )
        test_session.add(ws)

    await test_session.commit()

    # Execute aggregation query with GROUP BY on relationship path
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.WORK_SESSION,
        filters=[],
        aggregation=AggregationSpec(
            function=AggregationFunction.SUM,
            field="duration_hours",
            group_by=["project.name"],
        ),
    )

    assert result["entity_type"] == "work_session"
    assert "aggregation" in result
    assert result["aggregation"]["function"] == "sum"
    assert result["total_groups"] == 2

    # Validate per-group totals (not global totals)
    groups = result["aggregation"]["groups"]
    alpha_result = next((g for g in groups if g["group_values"][0] == "Project Alpha"), None)
    beta_result = next((g for g in groups if g["group_values"][0] == "Project Beta"), None)

    assert alpha_result is not None
    assert beta_result is not None
    assert alpha_result["result"] == Decimal("24.0")
    assert beta_result["result"] == Decimal("10.0")


@pytest.mark.asyncio
async def test_filter_by_project_id(test_session):
    """Test filtering by simple project_id field."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    project = Project(
        name="Specific Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.flush()

    ws = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("8.0"),
        summary="Specific work",
        privacy_level=PrivacyLevel.PUBLIC,
    )
    test_session.add(ws)
    await test_session.commit()

    # Execute query filtering by project_id
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.WORK_SESSION,
        filters=[FilterSpec(field="project_id", operator=FilterOperator.EQ, value=project.id)],
    )

    assert result["entity_type"] == "work_session"
    assert result["total_count"] >= 1
    assert result["results"][0].project_id == project.id
    assert result["results"][0].description == "Specific work"


@pytest.mark.asyncio
async def test_filter_by_has_tag(test_session):
    """Test HAS_TAG operator with PostgreSQL array column."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    project = Project(
        name="Test Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add(project)
    await test_session.flush()

    # Create work sessions with different tags
    ws1 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("8.0"),
        summary="Frontend work",
        privacy_level=PrivacyLevel.PUBLIC,
        tags=["frontend", "react"],
    )
    ws2 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 16),
        start_time=datetime(2024, 1, 16, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 16, 17, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("8.0"),
        summary="Backend work",
        privacy_level=PrivacyLevel.PUBLIC,
        tags=["backend", "api"],
    )
    ws3 = WorkSession(
        project_id=project.id,
        date=date(2024, 1, 17),
        start_time=datetime(2024, 1, 17, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 17, 17, 0, tzinfo=timezone.utc),
        duration_hours=Decimal("8.0"),
        summary="Full stack work",
        privacy_level=PrivacyLevel.PUBLIC,
        tags=["frontend", "backend"],
    )
    test_session.add_all([ws1, ws2, ws3])
    await test_session.commit()

    # Execute query filtering by single tag
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.WORK_SESSION,
        filters=[FilterSpec(field="tags", operator=FilterOperator.HAS_TAG, value="frontend")],
    )

    assert result["entity_type"] == "work_session"
    assert result["total_count"] == 2  # ws1 and ws3 have "frontend" tag
    descriptions = [ws.description for ws in result["results"]]
    assert "Frontend work" in descriptions
    assert "Full stack work" in descriptions
    assert "Backend work" not in descriptions


@pytest.mark.asyncio
async def test_filter_by_on_behalf_of_null(test_session):
    """Test field name mapping: on_behalf_of (schema) -> on_behalf_of_id (model)."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    # Create projects with and without employer
    project_with_employer = Project(
        name="Corporate Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    project_without_employer = Project(
        name="Personal Project",
        client_id=client.id,
        on_behalf_of_id=None,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add_all([project_with_employer, project_without_employer])
    await test_session.commit()

    # Query using schema field name "on_behalf_of" with IS_NULL
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.PROJECT,
        filters=[FilterSpec(field="on_behalf_of", operator=FilterOperator.IS_NULL, value=None)],
    )

    assert result["entity_type"] == "project"
    assert result["total_count"] == 1
    assert result["results"][0].name == "Personal Project"
    assert result["results"][0].on_behalf_of is None


@pytest.mark.asyncio
async def test_filter_by_on_behalf_of_not_null(test_session):
    """Test field name mapping with IS_NOT_NULL operator."""
    # Create required dependencies
    client = Client(name="Test Client", type=ClientType.COMPANY, status=ClientStatus.ACTIVE)
    test_session.add(client)
    await test_session.flush()

    employer = Employer(name="Test Employer", is_current=True)
    test_session.add(employer)
    await test_session.flush()

    # Create projects with and without employer
    project_with_employer = Project(
        name="Corporate Project",
        client_id=client.id,
        on_behalf_of_id=employer.id,
        status=ProjectStatus.ACTIVE,
    )
    project_without_employer = Project(
        name="Personal Project",
        client_id=client.id,
        on_behalf_of_id=None,
        status=ProjectStatus.ACTIVE,
    )
    test_session.add_all([project_with_employer, project_without_employer])
    await test_session.commit()

    # Query using schema field name "on_behalf_of" with IS_NOT_NULL
    service = QueryService(test_session)
    result = await service.structured_query(
        entity_type=EntityType.PROJECT,
        filters=[FilterSpec(field="on_behalf_of", operator=FilterOperator.IS_NOT_NULL, value=None)],
    )

    assert result["entity_type"] == "project"
    assert result["total_count"] == 1
    assert result["results"][0].name == "Corporate Project"
    assert result["results"][0].on_behalf_of == employer.id
