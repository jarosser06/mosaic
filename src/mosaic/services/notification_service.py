"""Service layer for sending desktop notifications."""

import logging
from typing import Any

from desktop_notifier import DEFAULT_SOUND, DesktopNotifier, Urgency

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Business logic for sending desktop notifications.

    Uses desktop-notifier library for cross-platform notifications
    (macOS, Windows, Linux).

    IMPORTANT (macOS 10.14+):
        Requires a SIGNED Python executable. Homebrew Python is NOT signed.
        Use python.org installer or sign manually:
            codesign -s - $(which python3)

        Without signing, notifications silently fail (no error raised).
    """

    def __init__(self, app_name: str = "Mosaic") -> None:
        """
        Initialize NotificationService with desktop notifier.

        Args:
            app_name: Application name to display in notifications
        """
        self.notifier = DesktopNotifier(app_name=app_name)
        self._capabilities_checked = False
        self._notifications_available = True

    async def check_capabilities(self) -> frozenset[str] | dict[str, bool]:
        """
        Check desktop notification capabilities.

        Returns:
            frozenset or dict: Supported features (varies by platform)

        Note:
            On macOS 10.14+, this doesn't detect unsigned executable issue.
            Notifications will appear to work but fail silently.
        """
        if not self._capabilities_checked:
            try:
                capabilities = await self.notifier.get_capabilities()
                self._capabilities_checked = True
                logger.info(f"Notification capabilities: {capabilities}")
                return capabilities  # type: ignore[return-value]
            except Exception as e:
                logger.warning(f"Could not check notification capabilities: {e}")
                self._notifications_available = False
                return frozenset()
        return frozenset()

    async def trigger_notification(
        self,
        title: str,
        message: str,
        sound: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send a desktop notification.

        Args:
            title: Notification title
            message: Notification message body
            sound: Notification sound ("default" or "none")
            metadata: Optional metadata (logged but not displayed)

        Returns:
            bool: True if send() completed without exception, False otherwise

        Warning:
            On macOS 10.14+, may return True even if notification doesn't show
            due to unsigned Python executable. See class docstring for fix.

        Note:
            Metadata is logged but not included in the notification itself.
            Desktop notifications have limited display capabilities.
        """
        try:
            # Log metadata if provided
            if metadata:
                logger.debug(f"Notification metadata: {metadata}")

            # Determine sound setting
            notification_sound = DEFAULT_SOUND if sound == "default" else None

            # Send notification
            await self.notifier.send(
                title=title,
                message=message,
                urgency=Urgency.Normal,
                sound=notification_sound,
            )

            logger.info(f"Sent notification: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}", exc_info=True)
            self._notifications_available = False
            return False
