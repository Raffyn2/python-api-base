"""Tests for notification service module.

**Feature: realistic-test-coverage**
**Validates: Requirements 8.1, 8.4, 8.7**
"""

from dataclasses import dataclass

import pytest

from core.base.patterns.result import Err, Ok, Result
from infrastructure.messaging.notification.models import (
    Notification,
    NotificationError,
    NotificationStatus,
    UserPreferences,
)
from infrastructure.messaging.notification.service import NotificationService


@dataclass
class EmailPayload:
    """Email payload for testing."""

    subject: str
    body: str


class MockChannel:
    """Mock notification channel for testing."""

    def __init__(
        self,
        should_fail: bool = False,
        error: NotificationError = NotificationError.CHANNEL_ERROR,
    ) -> None:
        self._should_fail = should_fail
        self._error = error
        self._sent: list[tuple[str, EmailPayload]] = []

    async def send(
        self, recipient: str, payload: EmailPayload
    ) -> Result[NotificationStatus, NotificationError]:
        if self._should_fail:
            return Err(self._error)
        self._sent.append((recipient, payload))
        return Ok(NotificationStatus.SENT)

    async def send_batch(
        self, messages: list[tuple[str, EmailPayload]]
    ) -> list[Result[NotificationStatus, NotificationError]]:
        results = []
        for recipient, payload in messages:
            results.append(await self.send(recipient, payload))
        return results


class TestNotificationService:
    """Tests for NotificationService."""

    def test_register_channel(self) -> None:
        """Test registering a channel."""
        service = NotificationService[EmailPayload]()
        channel = MockChannel()
        
        service.register_channel("email", channel)
        
        assert "email" in service._channels

    def test_set_preferences(self) -> None:
        """Test setting user preferences."""
        service = NotificationService[EmailPayload]()
        prefs = UserPreferences(user_id="user-123", email_enabled=False)
        
        service.set_preferences(prefs)
        
        result = service.get_preferences("user-123")
        assert result is not None
        assert result.email_enabled is False

    def test_get_preferences_not_found(self) -> None:
        """Test getting non-existent preferences."""
        service = NotificationService[EmailPayload]()
        result = service.get_preferences("non-existent")
        assert result is None

    def test_is_opted_out_no_preferences(self) -> None:
        """Test opt-out check with no preferences."""
        service = NotificationService[EmailPayload]()
        result = service.is_opted_out("user-123", "email")
        assert result is False

    def test_is_opted_out_email_disabled(self) -> None:
        """Test opt-out when email is disabled."""
        service = NotificationService[EmailPayload]()
        prefs = UserPreferences(user_id="user-123", email_enabled=False)
        service.set_preferences(prefs)
        
        result = service.is_opted_out("user-123", "email")
        assert result is True

    def test_is_opted_out_sms_disabled(self) -> None:
        """Test opt-out when SMS is disabled."""
        service = NotificationService[EmailPayload]()
        prefs = UserPreferences(user_id="user-123", sms_enabled=False)
        service.set_preferences(prefs)
        
        result = service.is_opted_out("user-123", "sms")
        assert result is True

    def test_is_opted_out_push_disabled(self) -> None:
        """Test opt-out when push is disabled."""
        service = NotificationService[EmailPayload]()
        prefs = UserPreferences(user_id="user-123", push_enabled=False)
        service.set_preferences(prefs)
        
        result = service.is_opted_out("user-123", "push")
        assert result is True

    def test_is_opted_out_channel_in_list(self) -> None:
        """Test opt-out when channel is in opted_out_channels."""
        service = NotificationService[EmailPayload]()
        prefs = UserPreferences(
            user_id="user-123",
            opted_out_channels=frozenset(["marketing"]),
        )
        service.set_preferences(prefs)
        
        result = service.is_opted_out("user-123", "marketing")
        assert result is True

    def test_is_rate_limited_under_limit(self) -> None:
        """Test rate limit check under limit."""
        service = NotificationService[EmailPayload]()
        result = service.is_rate_limited("user-123")
        assert result is False

    def test_is_rate_limited_at_limit(self) -> None:
        """Test rate limit check at limit."""
        service = NotificationService[EmailPayload]()
        service._rate_limits["user-123"] = 100
        
        result = service.is_rate_limited("user-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_send_success(self) -> None:
        """Test successful notification send."""
        service = NotificationService[EmailPayload]()
        channel = MockChannel()
        service.register_channel("email", channel)
        
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        payload = EmailPayload(subject="Welcome", body="Hello!")
        
        result = await service.send(notification, payload)
        
        assert result.is_ok()
        assert result.unwrap() == NotificationStatus.SENT

    @pytest.mark.asyncio
    async def test_send_opt_out(self) -> None:
        """Test send blocked by opt-out."""
        service = NotificationService[EmailPayload]()
        channel = MockChannel()
        service.register_channel("email", channel)
        
        prefs = UserPreferences(user_id="user-456", email_enabled=False)
        service.set_preferences(prefs)
        
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        payload = EmailPayload(subject="Welcome", body="Hello!")
        
        result = await service.send(notification, payload)
        
        assert result.is_err()
        assert result.error == NotificationError.OPT_OUT

    @pytest.mark.asyncio
    async def test_send_rate_limited(self) -> None:
        """Test send blocked by rate limit."""
        service = NotificationService[EmailPayload]()
        channel = MockChannel()
        service.register_channel("email", channel)
        service._rate_limits["user-456"] = 100
        
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        payload = EmailPayload(subject="Welcome", body="Hello!")
        
        result = await service.send(notification, payload)
        
        assert result.is_err()
        assert result.error == NotificationError.RATE_LIMITED

    @pytest.mark.asyncio
    async def test_send_channel_not_found(self) -> None:
        """Test send with unknown channel."""
        service = NotificationService[EmailPayload]()
        
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="unknown",
            template_id="welcome",
            context={},
        )
        payload = EmailPayload(subject="Welcome", body="Hello!")
        
        result = await service.send(notification, payload)
        
        assert result.is_err()
        assert result.error == NotificationError.CHANNEL_ERROR

    @pytest.mark.asyncio
    async def test_send_updates_rate_limit(self) -> None:
        """Test send updates rate limit counter."""
        service = NotificationService[EmailPayload]()
        channel = MockChannel()
        service.register_channel("email", channel)
        
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        payload = EmailPayload(subject="Welcome", body="Hello!")
        
        await service.send(notification, payload)
        
        assert service._rate_limits["user-456"] == 1

    @pytest.mark.asyncio
    async def test_send_batch(self) -> None:
        """Test sending batch of notifications."""
        service = NotificationService[EmailPayload]()
        channel = MockChannel()
        service.register_channel("email", channel)
        
        notifications = [
            (
                Notification(
                    id=f"notif-{i}",
                    recipient_id=f"user-{i}",
                    channel="email",
                    template_id="welcome",
                    context={},
                ),
                EmailPayload(subject="Welcome", body="Hello!"),
            )
            for i in range(3)
        ]
        
        results = await service.send_batch(notifications)
        
        assert len(results) == 3
        assert all(r.is_ok() for r in results)
