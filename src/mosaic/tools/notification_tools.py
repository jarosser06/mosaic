"""MCP tools for triggering notifications."""

import logging

from mcp.server.fastmcp import Context

from ..schemas.notification import TriggerNotificationInput, TriggerNotificationOutput
from ..server import mcp
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@mcp.tool()
async def trigger_notification(
    input: TriggerNotificationInput, ctx: Context
) -> TriggerNotificationOutput:
    """
    Trigger a macOS notification (internal tool).

    Sends a notification through the macOS notification bridge service.
    Used by the scheduler for reminder notifications.

    Args:
        input: Notification title and message
        ctx: MCP context with app resources

    Returns:
        TriggerNotificationOutput: Success status and message

    Raises:
        None (returns success=False on failure)
    """
    try:
        service = NotificationService()

        success = await service.trigger_notification(
            title=input.title,
            message=input.message,
        )

        if success:
            logger.info(f"Triggered notification: {input.title}")
            return TriggerNotificationOutput(success=True, message="Notification sent successfully")
        else:
            logger.warning(f"Failed to trigger notification: {input.title}")
            return TriggerNotificationOutput(
                success=False, message="Failed to reach notification bridge"
            )
    except Exception as e:
        logger.error(f"Error triggering notification: {e}", exc_info=True)
        return TriggerNotificationOutput(success=False, message=f"Error: {str(e)}")
