"""MCP tools for reminder management operations."""

import logging
from typing import Any

from mcp.server.fastmcp import Context

from ..repositories.reminder_repository import ReminderRepository
from ..schemas.reminder_management import (
    BulkCompleteRemindersInput,
    BulkCompleteRemindersOutput,
    DeleteReminderInput,
    DeleteReminderOutput,
    ListRemindersInput,
    ListRemindersOutput,
    ReminderItem,
    ReminderStatus,
)
from ..server import AppContext, mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def list_reminders(
    input: ListRemindersInput, ctx: Context[Any, AppContext, ListRemindersInput]
) -> ListRemindersOutput:
    """
    List and filter reminders.

    Retrieve reminders based on status (all, active, completed, snoozed),
    entity attachments, and tags. Useful for reviewing pending tasks,
    finding completed reminders, or managing snoozed notifications.

    Args:
        input: Filter criteria (status, entity_type, entity_id, tags)
        ctx: MCP context with app resources

    Returns:
        ListRemindersOutput: List of matching reminders with total count

    Raises:
        None (returns empty list if no matches)
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            # Start with base query - get all reminders
            from sqlalchemy import select

            from ..models.reminder import Reminder

            query = select(Reminder)

            # Apply status filter
            if input.status == ReminderStatus.ACTIVE:
                query = query.where(Reminder.is_completed == False)  # noqa: E712
                query = query.where(Reminder.snoozed_until.is_(None))
            elif input.status == ReminderStatus.COMPLETED:
                query = query.where(Reminder.is_completed == True)  # noqa: E712
            elif input.status == ReminderStatus.SNOOZED:
                query = query.where(Reminder.snoozed_until.isnot(None))
            # ALL status - no filter applied

            # Apply entity filters
            if input.entity_type is not None:
                query = query.where(Reminder.related_entity_type == input.entity_type)
            if input.entity_id is not None:
                query = query.where(Reminder.related_entity_id == input.entity_id)

            # Apply tag filter (reminders with ANY of the specified tags)
            if input.tags:
                from sqlalchemy import or_

                # Use PostgreSQL array overlap operator (&&)
                # Check if reminder tags array overlaps with filter tag
                tag_conditions = [Reminder.tags.op("&&")([tag]) for tag in input.tags]
                query = query.where(or_(*tag_conditions))

            # Execute query
            result = await session.execute(query)
            reminders = list(result.scalars().all())

            # Convert to output schema
            reminder_items = [
                ReminderItem(
                    id=r.id,
                    reminder_time=r.reminder_time,
                    message=r.message,
                    entity_type=r.related_entity_type,
                    entity_id=r.related_entity_id,
                    completed_at=r.updated_at if r.is_completed else None,
                    snoozed_until=r.snoozed_until,
                    tags=r.tags or [],
                    created_at=r.created_at,
                )
                for r in reminders
            ]

            logger.info(
                f"Listed {len(reminder_items)} reminders with status={input.status}, "
                f"entity_type={input.entity_type}, entity_id={input.entity_id}, tags={input.tags}"
            )

            return ListRemindersOutput(
                reminders=reminder_items,
                total_count=len(reminder_items),
            )
        except Exception as e:
            logger.error(f"Failed to list reminders: {e}", exc_info=True)
            raise


@mcp.tool()
async def delete_reminder(
    input: DeleteReminderInput, ctx: Context[Any, AppContext, DeleteReminderInput]
) -> DeleteReminderOutput:
    """
    Delete a reminder permanently.

    Removes a reminder from the system. This is irreversible.
    Use complete_reminder if you want to keep the record.

    Args:
        input: Reminder ID to delete
        ctx: MCP context with app resources

    Returns:
        DeleteReminderOutput: Success status and confirmation message

    Raises:
        ValueError: If reminder not found
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = ReminderRepository(session)

            # Check if reminder exists
            reminder = await repo.get_by_id(input.reminder_id)
            if not reminder:
                raise ValueError(f"Reminder with ID {input.reminder_id} not found")

            # Delete the reminder
            await repo.delete(input.reminder_id)

            # Commit transaction
            await session.commit()

            logger.info(f"Deleted reminder {input.reminder_id}")

            return DeleteReminderOutput(
                success=True,
                message=f"Reminder {input.reminder_id} deleted successfully",
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete reminder: {e}", exc_info=True)
            raise


@mcp.tool()
async def bulk_complete_reminders(
    input: BulkCompleteRemindersInput,
    ctx: Context[Any, AppContext, BulkCompleteRemindersInput],
) -> BulkCompleteRemindersOutput:
    """
    Mark multiple reminders as completed at once.

    Efficiently complete multiple reminders in a single operation.
    Useful for batch processing of notifications. Failed completions
    are tracked and returned separately.

    Args:
        input: List of reminder IDs to complete
        ctx: MCP context with app resources

    Returns:
        BulkCompleteRemindersOutput: Count of completed/failed reminders and failed IDs

    Raises:
        None (individual failures are tracked in output)
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        try:
            repo = ReminderRepository(session)

            completed_count = 0
            failed_count = 0
            failed_ids: list[int] = []

            for reminder_id in input.reminder_ids:
                try:
                    # Mark as completed
                    updated_reminder = await repo.mark_completed(reminder_id)

                    if updated_reminder is None:
                        # Reminder not found
                        failed_count += 1
                        failed_ids.append(reminder_id)
                        logger.warning(f"Reminder {reminder_id} not found during bulk complete")
                    else:
                        completed_count += 1
                except Exception as e:
                    # Individual reminder failure
                    failed_count += 1
                    failed_ids.append(reminder_id)
                    logger.error(f"Failed to complete reminder {reminder_id}: {e}", exc_info=True)

            # Commit all successful completions
            await session.commit()

            # Generate summary message
            if failed_count == 0:
                message = f"Successfully completed {completed_count} reminders"
            else:
                message = (
                    f"Completed {completed_count} reminders, "
                    f"failed {failed_count} (IDs: {failed_ids})"
                )

            logger.info(
                f"Bulk completed {completed_count} reminders, "
                f"failed {failed_count} out of {len(input.reminder_ids)} total"
            )

            return BulkCompleteRemindersOutput(
                completed_count=completed_count,
                failed_count=failed_count,
                failed_ids=failed_ids,
                message=message,
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to bulk complete reminders: {e}", exc_info=True)
            raise
