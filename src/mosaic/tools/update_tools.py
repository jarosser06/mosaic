"""MCP tools for updating entities in Mosaic."""

import logging
from typing import Any

from mcp.server.fastmcp import Context

from ..repositories.client_repository import ClientRepository
from ..repositories.note_repository import NoteRepository
from ..repositories.person_repository import PersonRepository
from ..repositories.project_repository import ProjectRepository
from ..schemas.client import UpdateClientInput, UpdateClientOutput
from ..schemas.meeting import UpdateMeetingInput, UpdateMeetingOutput
from ..schemas.note import UpdateNoteInput, UpdateNoteOutput
from ..schemas.person import UpdatePersonInput, UpdatePersonOutput
from ..schemas.project import UpdateProjectInput, UpdateProjectOutput
from ..schemas.reminder import (
    CompleteReminderInput,
    CompleteReminderOutput,
    SnoozeReminderInput,
    SnoozeReminderOutput,
)
from ..schemas.work_session import UpdateWorkSessionInput, UpdateWorkSessionOutput
from ..server import mcp
from ..services.meeting_service import MeetingService
from ..services.reminder_service import ReminderService
from ..services.work_session_service import WorkSessionService

logger = logging.getLogger(__name__)


@mcp.tool()
async def update_work_session(
    work_session_id: int, input: UpdateWorkSessionInput, ctx: Context
) -> UpdateWorkSessionOutput:
    """
    Update an existing work session.

    Modifies work session fields. If start_time or end_time change,
    duration is automatically recalculated with half-hour rounding.

    Args:
        work_session_id: ID of work session to update
        input: Updated fields (only non-None fields are updated)
        ctx: MCP context with app resources

    Returns:
        UpdateWorkSessionOutput: Updated work session with recalculated duration

    Raises:
        ValueError: If work session not found or times are invalid
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            service = WorkSessionService(session)

            work_session = await service.update_work_session(
                work_session_id=work_session_id,
                start_time=input.start_time,
                end_time=input.end_time,
                summary=input.description,
                privacy_level=input.privacy_level,
            )

            # Update tags if provided
            if input.tags is not None:
                work_session.tags = input.tags

            # Update project_id if provided
            if input.project_id is not None:
                work_session.project_id = input.project_id

            # Flush and refresh to ensure all fields are up to date
            await session.flush()
            await session.refresh(work_session)

            # Commit transaction
            await session.commit()

            logger.info(f"Updated work session {work_session_id}")

            return UpdateWorkSessionOutput(
                id=work_session.id,
                start_time=work_session.start_time,
                end_time=work_session.end_time,
                project_id=work_session.project_id,
                duration_hours=work_session.duration_hours,
                description=work_session.summary,
                privacy_level=work_session.privacy_level,
                tags=work_session.tags or [],
                created_at=work_session.created_at,
                updated_at=work_session.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update work session: {e}", exc_info=True)
            raise


@mcp.tool()
async def update_meeting(
    meeting_id: int, input: UpdateMeetingInput, ctx: Context
) -> UpdateMeetingOutput:
    """
    Update an existing meeting.

    Modifies meeting fields including times, title, attendees, project,
    description, privacy, and tags.

    Args:
        meeting_id: ID of meeting to update
        input: Updated fields (only non-None fields are updated)
        ctx: MCP context with app resources

    Returns:
        UpdateMeetingOutput: Updated meeting record

    Raises:
        ValueError: If meeting not found or times are invalid
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            service = MeetingService(session)

            # Calculate new duration if times changed
            duration_minutes = None
            if input.start_time and input.end_time:
                duration_minutes = int((input.end_time - input.start_time).total_seconds() / 60)

            meeting = await service.update_meeting(
                meeting_id=meeting_id,
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

            logger.info(f"Updated meeting {meeting_id}")

            return UpdateMeetingOutput(
                id=meeting.id,
                start_time=meeting.start_time,
                end_time=input.end_time or meeting.start_time,
                title=input.title or meeting.title or "",
                attendees=input.attendees or [],
                project_id=meeting.project_id,
                description=meeting.summary,
                privacy_level=meeting.privacy_level,
                tags=meeting.tags or [],
                created_at=meeting.created_at,
                updated_at=meeting.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update meeting: {e}", exc_info=True)
            raise


@mcp.tool()
async def update_person(
    person_id: int, input: UpdatePersonInput, ctx: Context
) -> UpdatePersonOutput:
    """
    Update an existing person.

    Modifies person contact and professional information.

    Args:
        person_id: ID of person to update
        input: Updated fields (only non-None fields are updated)
        ctx: MCP context with app resources

    Returns:
        UpdatePersonOutput: Updated person record

    Raises:
        ValueError: If person not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = PersonRepository(session)

            update_data: dict[str, Any] = {}
            if input.full_name is not None:
                update_data["full_name"] = input.full_name
            if input.email is not None:
                update_data["email"] = input.email
            if input.phone is not None:
                update_data["phone"] = input.phone
            if input.company is not None:
                update_data["company"] = input.company
            if input.title is not None:
                update_data["title"] = input.title
            if input.notes is not None:
                update_data["notes"] = input.notes
            if input.tags is not None:
                update_data["tags"] = input.tags

            person = await repo.update(person_id, **update_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Updated person {person_id}")

            return UpdatePersonOutput(
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
            logger.error(f"Failed to update person: {e}", exc_info=True)
            raise


@mcp.tool()
async def update_client(
    client_id: int, input: UpdateClientInput, ctx: Context
) -> UpdateClientOutput:
    """
    Update an existing client.

    Modifies client information including name, type, status, contact person,
    and notes.

    Args:
        client_id: ID of client to update
        input: Updated fields (only non-None fields are updated)
        ctx: MCP context with app resources

    Returns:
        UpdateClientOutput: Updated client record

    Raises:
        ValueError: If client not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = ClientRepository(session)

            update_data: dict[str, Any] = {}
            if input.name is not None:
                update_data["name"] = input.name
            if input.client_type is not None:
                # Map schema field client_type to model field type
                update_data["type"] = input.client_type
            if input.status is not None:
                update_data["status"] = input.status
            if input.contact_person_id is not None:
                update_data["contact_person_id"] = input.contact_person_id
            if input.notes is not None:
                update_data["notes"] = input.notes
            if input.tags is not None:
                update_data["tags"] = input.tags

            client = await repo.update(client_id, **update_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Updated client {client_id}")

            return UpdateClientOutput(
                id=client.id,
                name=client.name,
                # Map model field type to schema field client_type
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
            logger.error(f"Failed to update client: {e}", exc_info=True)
            raise


@mcp.tool()
async def update_project(
    project_id: int, input: UpdateProjectInput, ctx: Context
) -> UpdateProjectOutput:
    """
    Update an existing project.

    Modifies project information including name, client, status, on_behalf_of,
    description, and tags.

    Args:
        project_id: ID of project to update
        input: Updated fields (only non-None fields are updated)
        ctx: MCP context with app resources

    Returns:
        UpdateProjectOutput: Updated project record

    Raises:
        ValueError: If project not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = ProjectRepository(session)

            update_data: dict[str, Any] = {}
            if input.name is not None:
                update_data["name"] = input.name
            if input.client_id is not None:
                update_data["client_id"] = input.client_id
            if input.status is not None:
                update_data["status"] = input.status
            if input.on_behalf_of is not None:
                # Map schema field on_behalf_of to model field on_behalf_of_id
                update_data["on_behalf_of_id"] = input.on_behalf_of
            if input.description is not None:
                update_data["description"] = input.description
            if input.tags is not None:
                update_data["tags"] = input.tags

            project = await repo.update(project_id, **update_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Updated project {project_id}")

            return UpdateProjectOutput(
                id=project.id,
                name=project.name,
                client_id=project.client_id,
                status=project.status,
                # Map model field on_behalf_of_id to schema field on_behalf_of
                on_behalf_of=project.on_behalf_of_id,
                description=project.description,
                tags=project.tags or [],
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update project: {e}", exc_info=True)
            raise


@mcp.tool()
async def update_note(note_id: int, input: UpdateNoteInput, ctx: Context) -> UpdateNoteOutput:
    """
    Update an existing note.

    Modifies note content, entity attachment, privacy level, and tags.

    Args:
        note_id: ID of note to update
        input: Updated fields (only non-None fields are updated)
        ctx: MCP context with app resources

    Returns:
        UpdateNoteOutput: Updated note record

    Raises:
        ValueError: If note not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = NoteRepository(session)

            update_data: dict[str, Any] = {}
            if input.content is not None:
                # Map schema field content to model field text
                update_data["text"] = input.content
            if input.entity_type is not None:
                update_data["entity_type"] = input.entity_type
            if input.entity_id is not None:
                update_data["entity_id"] = input.entity_id
            if input.privacy_level is not None:
                update_data["privacy_level"] = input.privacy_level
            if input.tags is not None:
                update_data["tags"] = input.tags

            note = await repo.update(note_id, **update_data)

            # Commit transaction
            await session.commit()

            logger.info(f"Updated note {note_id}")

            return UpdateNoteOutput(
                id=note.id,
                # Map model field text to schema field content
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
            logger.error(f"Failed to update note: {e}", exc_info=True)
            raise


@mcp.tool()
async def complete_reminder(input: CompleteReminderInput, ctx: Context) -> CompleteReminderOutput:
    """
    Mark a reminder as completed.

    Sets the completed_at timestamp to now and prevents future notifications.
    For recurring reminders, creates the next occurrence and returns it.

    Args:
        input: Reminder ID to complete
        ctx: MCP context with app resources

    Returns:
        CompleteReminderOutput: Next occurrence for recurring reminders,
            or completed reminder for non-recurring

    Raises:
        ValueError: If reminder not found or already completed
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            service = ReminderService(session)

            # Get the original reminder before completing it
            from ..repositories.reminder_repository import ReminderRepository

            repo = ReminderRepository(session)
            original_reminder = await repo.get_by_id(input.reminder_id)
            if not original_reminder:
                raise ValueError(f"Reminder with ID {input.reminder_id} not found")

            # Complete the reminder (returns next occurrence if recurring, None if not)
            next_reminder = await service.complete_reminder(input.reminder_id)

            # Commit transaction
            await session.commit()

            logger.info(f"Completed reminder {input.reminder_id}")

            # Return next occurrence if it exists, otherwise return the completed reminder
            reminder_to_return = next_reminder if next_reminder else original_reminder
            await session.refresh(reminder_to_return)

            return CompleteReminderOutput(
                id=reminder_to_return.id,
                reminder_time=reminder_to_return.reminder_time,
                message=reminder_to_return.message,
                entity_type=reminder_to_return.related_entity_type,
                entity_id=reminder_to_return.related_entity_id,
                completed_at=(
                    reminder_to_return.updated_at if reminder_to_return.is_completed else None
                ),
                snoozed_until=reminder_to_return.snoozed_until,
                tags=reminder_to_return.tags or [],
                created_at=reminder_to_return.created_at,
                updated_at=reminder_to_return.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to complete reminder: {e}", exc_info=True)
            raise


@mcp.tool()
async def snooze_reminder(input: SnoozeReminderInput, ctx: Context) -> SnoozeReminderOutput:
    """
    Snooze a reminder to a new time.

    Updates the snoozed_until timestamp to delay the reminder notification.

    Args:
        input: Reminder ID and new snooze time
        ctx: MCP context with app resources

    Returns:
        SnoozeReminderOutput: Snoozed reminder record

    Raises:
        ValueError: If reminder not found or already completed
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            service = ReminderService(session)

            reminder = await service.snooze_reminder(input.reminder_id, input.snooze_until)

            # Commit transaction
            await session.commit()

            logger.info(f"Snoozed reminder {input.reminder_id} until {input.snooze_until}")

            return SnoozeReminderOutput(
                id=reminder.id,
                reminder_time=reminder.reminder_time,
                message=reminder.message,
                entity_type=reminder.related_entity_type,
                entity_id=reminder.related_entity_id,
                completed_at=reminder.updated_at if reminder.is_completed else None,
                snoozed_until=reminder.snoozed_until,
                tags=reminder.tags or [],
                created_at=reminder.created_at,
                updated_at=reminder.updated_at,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to snooze reminder: {e}", exc_info=True)
            raise
