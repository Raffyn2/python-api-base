"""Tests for notification models module.

**Feature: realistic-test-coverage**
**Validates: Requirements 8.8, 8.9, 8.10**
"""

from datetime import datetime

import pytest

from infrastructure.messaging.notification.models import (
    Notification,
    NotificationError,
    NotificationStatus,
    UserPreferences,
)


class TestNotificationStatus:
    """Tests for NotificationStatus enum."""

    def test_pending_value(self) -> None:
        """Test PENDING status value."""
        assert NotificationStatus.PENDING.value == "pending"

    def test_sent_value(self) -> None:
        """Test SENT status value."""
        assert NotificationStatus.SENT.value == "sent"

    def test_delivered_value(self) -> None:
        """Test DELIVERED status value."""
        assert NotificationStatus.DELIVERED.value == "delivered"

    def test_read_value(self) -> None:
        """Test READ status value."""
        assert NotificationStatus.READ.value == "read"

    def test_failed_value(self) -> None:
        """Test FAILED status value."""
        assert NotificationStatus.FAILED.value == "failed"

    def test_skipped_value(self) -> None:
        """Test SKIPPED status value."""
        assert NotificationStatus.SKIPPED.value == "skipped"


class TestNotificationError:
    """Tests for NotificationError enum."""

    def test_invalid_recipient_value(self) -> None:
        """Test INVALID_RECIPIENT error value."""
        assert NotificationError.INVALID_RECIPIENT.value == "invalid_recipient"

    def test_template_error_value(self) -> None:
        """Test TEMPLATE_ERROR error value."""
        assert NotificationError.TEMPLATE_ERROR.value == "template_error"

    def test_channel_error_value(self) -> None:
        """Test CHANNEL_ERROR error value."""
        assert NotificationError.CHANNEL_ERROR.value == "channel_error"

    def test_rate_limited_value(self) -> None:
        """Test RATE_LIMITED error value."""
        assert NotificationError.RATE_LIMITED.value == "rate_limited"

    def test_opt_out_value(self) -> None:
        """Test OPT_OUT error value."""
        assert NotificationError.OPT_OUT.value == "opt_out"


class TestNotification:
    """Tests for Notification dataclass."""

    def test_create_notification(self) -> None:
        """Test creating a notification."""
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={"name": "John"},
        )
        assert notification.id == "notif-123"
        assert notification.recipient_id == "user-456"
        assert notification.channel == "email"
        assert notification.template_id == "welcome"
        assert notification.context == {"name": "John"}

    def test_default_status(self) -> None:
        """Test default status is PENDING."""
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        assert notification.status == NotificationStatus.PENDING

    def test_default_sent_at(self) -> None:
        """Test default sent_at is None."""
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        assert notification.sent_at is None

    def test_default_error(self) -> None:
        """Test default error is None."""
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        assert notification.error is None

    def test_notification_is_frozen(self) -> None:
        """Test notification is immutable."""
        notification = Notification(
            id="notif-123",
            recipient_id="user-456",
            channel="email",
            template_id="welcome",
            context={},
        )
        with pytest.raises(AttributeError):
            notification.id = "new-id"


class TestUserPreferences:
    """Tests for UserPreferences dataclass."""

    def test_create_preferences(self) -> None:
        """Test creating user preferences."""
        prefs = UserPreferences(
            user_id="user-123",
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
        )
        assert prefs.user_id == "user-123"
        assert prefs.email_enabled is True
        assert prefs.sms_enabled is False
        assert prefs.push_enabled is True

    def test_default_values(self) -> None:
        """Test default values."""
        prefs = UserPreferences(user_id="user-123")
        assert prefs.email_enabled is True
        assert prefs.sms_enabled is True
        assert prefs.push_enabled is True
        assert prefs.opted_out_channels == frozenset()

    def test_opted_out_channels(self) -> None:
        """Test opted out channels."""
        prefs = UserPreferences(
            user_id="user-123",
            opted_out_channels=frozenset(["marketing", "promotions"]),
        )
        assert "marketing" in prefs.opted_out_channels
        assert "promotions" in prefs.opted_out_channels

    def test_preferences_is_frozen(self) -> None:
        """Test preferences is immutable."""
        prefs = UserPreferences(user_id="user-123")
        with pytest.raises(AttributeError):
            prefs.user_id = "new-id"
