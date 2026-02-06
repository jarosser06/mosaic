"""MCP tools for logging/adding entities to Mosaic."""

import logging
from typing import Any

from mcp.server.fastmcp import Context

from ..repositories.client_repository import ClientRepository
from ..repositories.employer_repository import EmployerRepository
from ..repositories.meeting_repository import MeetingRepository
from ..repositories.note_repository import NoteRepository
from ..repositories.person_repository import PersonRepository
from ..repositories.project_repository import ProjectRepository
from ..repositories.work_session_repository import WorkSessionRepository
from ..schemas.client import AddClientInput, AddClientOutput
from ..schemas.employer import AddEmployerInput, AddEmployerOutput
from ..schemas.meeting import (
    DeleteMeetingInput,
    DeleteMeetingOutput,
    LogMeetingInput,
    LogMeetingOutput,
)
from ..schemas.note import AddNoteInput, AddNoteOutput
from ..schemas.person import AddPersonInput, AddPersonOutput
from ..schemas.project import AddProjectInput, AddProjectOutput
from ..schemas.reminder import AddReminderInput, AddReminderOutput
from ..schemas.work_session import (
    DeleteWorkSessionInput,
    DeleteWorkSessionOutput,
    LogWorkSessionInput,
    LogWorkSessionOutput,
)
from ..server import AppContext, mcp
from ..services.meeting_service import MeetingService
from ..services.work_session_service import WorkSessionService

logger = logging.getLogger(__name__)


@mcp.tool()
async def log_work_session(
    input: LogWorkSessionInput, ctx: Context[Any, AppContext, Any]
) -> LogWorkSessionOutput:
    """
    Log a work session.

    Creates a work session record with date, duration, project association,
    and optional description.

    Args:
        input: Work session details (date, duration, project, description, privacy)
        ctx: MCP context with app resources

    Returns:
        LogWorkSessionOutput: Created work session

    Raises:
        ValueError: If duration is invalid or project doesn't exist
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            service = WorkSessionService(session)

            work_session = await service.create_work_session(
                project_id=input.project_id,
                date=input.date,
                duration_hours=input.duration_hours,
                summary=input.description,
                privacy_level=input.privacy_level,
                tags=input.tags,
            )

            # Commit transaction
            await session.commit()

            logger.info(f"Created work session {work_session.id} for project {input.project_id}")

            return LogWorkSessionOutput(
                id=work_session.id,
                project_id=work_session.project_id,
                date=work_session.date,
                duration_hours=work_session.duration_hours,
                description=work_session.summary,
                privacy_level=work_session.privacy_level,
                tags=work_session.tags or [],
                created_at=work_session.created_at,
                updated_at=work_session.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to log work session: {e}", exc_info=True)
            raise


@mcp.tool()
async def log_meeting(
    input: LogMeetingInput, ctx: Context[Any, AppContext, Any]
) -> LogMeetingOutput:
    """
    Log a meeting with attendees and optional project association.

    Creates a meeting record with start/end times, title, attendees list,
    and optional project link. If project has on_behalf_of set, automatically
    creates a work session.

    Args:
        input: Meeting details (times, title, attendees, project, description)
        ctx: MCP context with app resources

    Returns:
        LogMeetingOutput: Created meeting record

    Raises:
        ValueError: If times are invalid or references don't exist
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            service = MeetingService(session)

            # Calculate duration in minutes
            duration_minutes = int((input.end_time - input.start_time).total_seconds() / 60)

            meeting = await service.create_meeting(
                start_time=input.start_time,
                duration_minutes=duration_minutes,
                title=input.title,
                summary=input.description,
                privacy_level=input.privacy_level,
                project_id=input.project_id,
                attendee_ids=input.attendees,
                tags=input.tags,
            )

            # Commit transaction
            await session.commit()

            logger.info(f"Created meeting {meeting.id}: {input.title}")

            return LogMeetingOutput(
                id=meeting.id,
                start_time=meeting.start_time,
                end_time=input.end_time,
                title=input.title,
                attendees=input.attendees,
                project_id=meeting.project_id,
                description=meeting.summary,
                privacy_level=meeting.privacy_level,
                tags=meeting.tags or [],
                created_at=meeting.created_at,
                updated_at=meeting.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to log meeting: {e}", exc_info=True)
            raise


@mcp.tool()
async def add_person(input: AddPersonInput, ctx: Context[Any, AppContext, Any]) -> AddPersonOutput:
    """
    Add a person to the contact database.

    Creates a person record with contact information (name, email, phone),
    professional details (company, title), and optional notes.

    Args:
        input: Person details (name, email, phone, company, title, notes)
        ctx: MCP context with app resources

    Returns:
        AddPersonOutput: Created person record

    Raises:
        ValueError: If validation fails
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = PersonRepository(session)

            person_data: dict[str, Any] = {
                "full_name": input.full_name,
                "email": input.email,
                "phone": input.phone,
                "company": input.company,
                "title": input.title,
                "notes": input.notes,
                "tags": input.tags,
            }

            person = await repo.create(**person_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Created person {person.id}: {input.full_name}")

            return AddPersonOutput(
                id=person.id,
                full_name=person.full_name,
                email=person.email,
                phone=person.phone,
                company=person.company,
                title=person.title,
                notes=person.notes,
                tags=person.tags or [],
                created_at=person.created_at,
                updated_at=person.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add person: {e}", exc_info=True)
            raise


@mcp.tool()
async def add_client(input: AddClientInput, ctx: Context[Any, AppContext, Any]) -> AddClientOutput:
    """
    Add a client organization or individual.

    Creates a client record with type (company/individual), status (active/past),
    optional contact person, and notes.

    Args:
        input: Client details (name, type, status, contact, notes)
        ctx: MCP context with app resources

    Returns:
        AddClientOutput: Created client record

    Raises:
        ValueError: If validation fails or contact person doesn't exist
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = ClientRepository(session)

            client_data: dict[str, Any] = {
                "name": input.name,
                "type": input.client_type,
                "status": input.status,
                "contact_person_id": input.contact_person_id,
                "notes": input.notes,
                "tags": input.tags,
            }

            client = await repo.create(**client_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Created client {client.id}: {input.name}")

            return AddClientOutput(
                id=client.id,
                name=client.name,
                client_type=client.type,
                status=client.status,
                contact_person_id=client.contact_person_id,
                notes=client.notes,
                tags=client.tags or [],
                created_at=client.created_at,
                updated_at=client.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add client: {e}", exc_info=True)
            raise


@mcp.tool()
async def add_project(
    input: AddProjectInput, ctx: Context[Any, AppContext, Any]
) -> AddProjectOutput:
    """
    Add a project for a client.

    Creates a project record with client association, status (active/paused/completed),
    optional on_behalf_of for work attribution, and description.

    Args:
        input: Project details (name, client, status, on_behalf_of, description)
        ctx: MCP context with app resources

    Returns:
        AddProjectOutput: Created project record

    Raises:
        ValueError: If validation fails or client doesn't exist
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = ProjectRepository(session)

            project_data: dict[str, Any] = {
                "name": input.name,
                "client_id": input.client_id,
                "status": input.status,
                "on_behalf_of_id": input.on_behalf_of,
                "description": input.description,
                "tags": input.tags,
            }

            project = await repo.create(**project_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Created project {project.id}: {input.name}")

            return AddProjectOutput(
                id=project.id,
                name=project.name,
                client_id=project.client_id,
                status=project.status,
                on_behalf_of=project.on_behalf_of_id,
                description=project.description,
                tags=project.tags or [],
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add project: {e}", exc_info=True)
            raise


@mcp.tool()
async def add_employer(
    input: AddEmployerInput, ctx: Context[Any, AppContext, Any]
) -> AddEmployerOutput:
    """
    Add an employer organization.

    Creates an employer record used for on_behalf_of relationships in projects
    and work attribution.

    Args:
        input: Employer details (name, notes)
        ctx: MCP context with app resources

    Returns:
        AddEmployerOutput: Created employer record

    Raises:
        ValueError: If validation fails
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = EmployerRepository(session)

            employer_data: dict[str, Any] = {
                "name": input.name,
                "notes": input.notes,
                "tags": input.tags,
            }

            employer = await repo.create(**employer_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Created employer {employer.id}: {input.name}")

            return AddEmployerOutput(
                id=employer.id,
                name=employer.name,
                notes=employer.notes,
                tags=employer.tags or [],
                created_at=employer.created_at,
                updated_at=employer.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add employer: {e}", exc_info=True)
            raise


@mcp.tool()
async def add_note(input: AddNoteInput, ctx: Context[Any, AppContext, Any]) -> AddNoteOutput:
    """
    Add a note (standalone or attached to an entity).

    Creates a note with text content, optional entity attachment
    (person, client, project, meeting), privacy level, and tags.

    Args:
        input: Note details (content, entity_type, entity_id, privacy)
        ctx: MCP context with app resources

    Returns:
        AddNoteOutput: Created note record

    Raises:
        ValueError: If validation fails or entity doesn't exist
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = NoteRepository(session)

            note_data: dict[str, Any] = {
                "text": input.content,
                "entity_type": input.entity_type,
                "entity_id": input.entity_id,
                "privacy_level": input.privacy_level,
                "tags": input.tags,
            }

            note = await repo.create(**note_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Created note {note.id}")

            return AddNoteOutput(
                id=note.id,
                content=note.text,
                entity_type=note.entity_type,
                entity_id=note.entity_id,
                privacy_level=note.privacy_level,
                tags=note.tags or [],
                created_at=note.created_at,
                updated_at=note.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add note: {e}", exc_info=True)
            raise


@mcp.tool()
async def add_reminder(
    input: AddReminderInput, ctx: Context[Any, AppContext, Any]
) -> AddReminderOutput:
    """
    Add a reminder with due time and optional entity attachment.

    Creates a reminder that will trigger at the specified time. The scheduler
    automatically checks for due reminders and sends notifications.

    Args:
        input: Reminder details (reminder_time, message, entity_type, entity_id)
        ctx: MCP context with app resources

    Returns:
        AddReminderOutput: Created reminder record

    Raises:
        ValueError: If validation fails or entity doesn't exist
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            from ..services.reminder_service import ReminderService

            service = ReminderService(session)

            reminder = await service.create_reminder(
                reminder_time=input.reminder_time,
                message=input.message,
                related_entity_type=input.entity_type,
                related_entity_id=input.entity_id,
                tags=input.tags,
            )

            # Commit transaction
            await session.commit()

            logger.info(f"Created reminder {reminder.id} for {input.reminder_time}")

            return AddReminderOutput(
                id=reminder.id,
                reminder_time=reminder.reminder_time,
                message=reminder.message,
                entity_type=reminder.related_entity_type,
                entity_id=reminder.related_entity_id,
                completed_at=None,
                snoozed_until=reminder.snoozed_until,
                tags=reminder.tags or [],
                created_at=reminder.created_at,
                updated_at=reminder.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add reminder: {e}", exc_info=True)
            raise


@mcp.tool()
async def delete_work_session(
    input: DeleteWorkSessionInput, ctx: Context[Any, AppContext, DeleteWorkSessionInput]
) -> DeleteWorkSessionOutput:
    """
    Delete a work session permanently.

    Removes a work session from the system. This is irreversible.

    Args:
        input: Work session ID to delete
        ctx: MCP context with app resources

    Returns:
        DeleteWorkSessionOutput: Success status and confirmation message

    Raises:
        ValueError: If work session not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = WorkSessionRepository(session)

            # Check if work session exists
            work_session = await repo.get_by_id(input.work_session_id)
            if not work_session:
                raise ValueError(f"Work session with ID {input.work_session_id} not found")

            # Delete the work session
            await repo.delete(input.work_session_id)

            # Commit transaction
            await session.commit()

            logger.info(f"Deleted work session {input.work_session_id}")

            return DeleteWorkSessionOutput(
                success=True,
                message=f"Work session {input.work_session_id} deleted successfully",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete work session: {e}", exc_info=True)
            raise


@mcp.tool()
async def delete_meeting(
    input: DeleteMeetingInput, ctx: Context[Any, AppContext, DeleteMeetingInput]
) -> DeleteMeetingOutput:
    """
    Delete a meeting permanently.

    Deletes the meeting and all associated attendees (CASCADE).
    This is irreversible.

    Args:
        input: Meeting ID to delete
        ctx: MCP context with app resources

    Returns:
        DeleteMeetingOutput: Success status and confirmation message

    Raises:
        ValueError: If meeting not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = MeetingRepository(session)

            # Check if meeting exists
            meeting = await repo.get_by_id(input.meeting_id)
            if not meeting:
                raise ValueError(f"Meeting with ID {input.meeting_id} not found")

            # Delete the meeting
            await repo.delete(input.meeting_id)

            # Commit transaction
            await session.commit()

            logger.info(f"Deleted meeting {input.meeting_id}")

            return DeleteMeetingOutput(
                success=True,
                message=f"Meeting {input.meeting_id} deleted successfully",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete meeting: {e}", exc_info=True)
            raise
