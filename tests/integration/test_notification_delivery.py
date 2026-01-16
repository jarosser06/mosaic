"""Integration tests for desktop notifications.

Tests desktop notification delivery using mocked DesktopNotifier.
Validates that notifications are sent with correct parameters.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.mosaic.services.notification_service import NotificationService


class TestNotificationDelivery:
    """Test desktop notification delivery."""

    @pytest.mark.asyncio
    async def test_trigger_notification_success(self):
        """Test successful notification delivery."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            result = await service.trigger_notification(
                title="Test Notification",
                message="Test message",
            )

            assert result is True
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["title"] == "Test Notification"
            assert call_kwargs["message"] == "Test message"

    @pytest.mark.asyncio
    async def test_trigger_notification_with_metadata(self):
        """Test notification delivery with metadata (logged only)."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            metadata = {"reminder_id": 42, "entity_type": "meeting"}
            result = await service.trigger_notification(
                title="Reminder",
                message="Meeting in 5 minutes",
                metadata=metadata,
            )

            assert result is True
            # Metadata is logged but not passed to notification
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_notification_with_sound(self):
        """Test notification delivery with default sound."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            result = await service.trigger_notification(
                title="Alert",
                message="Important message",
                sound="default",
            )

            assert result is True
            call_kwargs = mock_send.call_args.kwargs
            assert call_kwargs["sound"] is not None  # DEFAULT_SOUND is used

    @pytest.mark.asyncio
    async def test_trigger_notification_http_error_retries(self):
        """Test notification handles errors gracefully (no retry needed)."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            # Simulate failure
            mock_send.side_effect = Exception("Notification failed")

            result = await service.trigger_notification(
                title="Test",
                message="Test message",
            )

            # Should return False on error
            assert result is False
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_notification_network_error_retries(self):
        """Test notification handles network errors (no retry in desktop-notifier)."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("Network error")

            result = await service.trigger_notification(
                title="Test",
                message="Test message",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_trigger_notification_max_retries_exceeded(self):
        """Test notification returns False on persistent errors."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("Persistent error")

            result = await service.trigger_notification(
                title="Test",
                message="Test message",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_trigger_notification_timeout_retries(self):
        """Test notification handles timeout errors."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = TimeoutError("Timeout")

            result = await service.trigger_notification(
                title="Test",
                message="Test message",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_trigger_notification_exponential_backoff(self):
        """Test notification doesn't require backoff (desktop-notifier is synchronous)."""
        service = NotificationService()

        with patch.object(service.notifier, "send", new_callable=AsyncMock) as mock_send:
            result = await service.trigger_notification(
                title="Test",
                message="Test message",
            )

            # Desktop notifier sends immediately, no retries/backoff needed
            assert result is True
            mock_send.assert_called_once()
