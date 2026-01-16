"""Unit tests for NotificationService with desktop-notifier."""

from unittest.mock import AsyncMock, patch

import pytest

from src.mosaic.services.notification_service import NotificationService


class TestNotificationSending:
    """Test sending desktop notifications."""

    @pytest.mark.asyncio
    async def test_trigger_notification_success(self):
        """Test successful notification send."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            result = await service.trigger_notification(
                title="Test Title",
                message="Test Message",
            )

            assert result is True
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["title"] == "Test Title"
            assert call_kwargs["message"] == "Test Message"

    @pytest.mark.asyncio
    async def test_trigger_notification_with_custom_sound(self):
        """Test notification with default sound enabled."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            result = await service.trigger_notification(
                title="Alert",
                message="Important",
                sound="default",
            )

            assert result is True
            call_kwargs = mock_send.call_args.kwargs
            # DEFAULT_SOUND is used when sound="default"
            assert call_kwargs["sound"] is not None

    @pytest.mark.asyncio
    async def test_trigger_notification_with_metadata(self):
        """Test notification with metadata (logged but not sent)."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            metadata = {"reminder_id": 123, "entity_type": "project"}
            result = await service.trigger_notification(
                title="Reminder",
                message="Check project",
                metadata=metadata,
            )

            assert result is True
            # Metadata is logged but not included in notification
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_notification_no_sound(self):
        """Test notification with sound disabled."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            result = await service.trigger_notification(
                title="Silent Alert",
                message="No sound",
                sound="none",
            )

            assert result is True
            call_kwargs = mock_send.call_args.kwargs
            # None is used when sound is not "default"
            assert call_kwargs["sound"] is None


class TestErrorHandling:
    """Test error handling in notification service."""

    @pytest.mark.asyncio
    async def test_trigger_notification_handles_exception(self):
        """Test notification returns False on exception."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("Notification failed")

            result = await service.trigger_notification(
                title="Test",
                message="Test",
            )

            assert result is False
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_notification_handles_runtime_error(self):
        """Test notification handles runtime errors."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = RuntimeError("Desktop notifier not available")

            result = await service.trigger_notification(
                title="Test",
                message="Test",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_trigger_notification_handles_timeout(self):
        """Test notification handles timeout errors."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = TimeoutError("Notification timeout")

            result = await service.trigger_notification(
                title="Test",
                message="Test",
            )

            assert result is False


class TestDesktopNotifierConfiguration:
    """Test DesktopNotifier configuration."""

    def test_service_initialization_default_app_name(self):
        """Test service initializes with default app name."""
        service = NotificationService()
        assert service.notifier is not None

    def test_service_initialization_custom_app_name(self):
        """Test service can be initialized with custom app name."""
        service = NotificationService(app_name="Custom App")
        assert service.notifier is not None

    @pytest.mark.asyncio
    async def test_notification_uses_normal_urgency(self):
        """Test notifications use Normal urgency by default."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            await service.trigger_notification(
                title="Test",
                message="Test",
            )

            call_kwargs = mock_send.call_args.kwargs
            # Check urgency is set
            assert "urgency" in call_kwargs
