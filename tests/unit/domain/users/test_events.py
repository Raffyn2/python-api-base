"""Unit tests for domain/users/events/events.py.

Tests user domain events.

**Task 8.3: Create tests for user domain events**
**Requirements: 2.2**
"""

import pytest

from domain.users.events.events import (
    UserDeactivatedEvent,
    UserEmailChangedEvent,
    UserEmailVerifiedEvent,
    UserLoggedInEvent,
    UserPasswordChangedEvent,
    UserProfileUpdatedEvent,
    UserReactivatedEvent,
    UserRegisteredEvent,
)


class TestUserRegisteredEvent:
    """Tests for UserRegisteredEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserRegisteredEvent(user_id="user-123", email="test@example.com")

        assert event.user_id == "user-123"
        assert event.email == "test@example.com"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserRegisteredEvent(user_id="user-123", email="test@example.com")
        assert event.event_type == "user.registered"

    def test_immutability(self) -> None:
        """Test event is immutable."""
        event = UserRegisteredEvent(user_id="user-123", email="test@example.com")
        with pytest.raises(AttributeError):
            event.user_id = "new-id"


class TestUserDeactivatedEvent:
    """Tests for UserDeactivatedEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserDeactivatedEvent(user_id="user-123", reason="Violation")

        assert event.user_id == "user-123"
        assert event.reason == "Violation"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserDeactivatedEvent(user_id="user-123", reason="")
        assert event.event_type == "user.deactivated"


class TestUserEmailChangedEvent:
    """Tests for UserEmailChangedEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserEmailChangedEvent(
            user_id="user-123",
            old_email="old@example.com",
            new_email="new@example.com",
        )

        assert event.user_id == "user-123"
        assert event.old_email == "old@example.com"
        assert event.new_email == "new@example.com"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserEmailChangedEvent(
            user_id="user-123", old_email="", new_email=""
        )
        assert event.event_type == "user.email_changed"


class TestUserPasswordChangedEvent:
    """Tests for UserPasswordChangedEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserPasswordChangedEvent(user_id="user-123")
        assert event.user_id == "user-123"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserPasswordChangedEvent(user_id="user-123")
        assert event.event_type == "user.password_changed"


class TestUserEmailVerifiedEvent:
    """Tests for UserEmailVerifiedEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserEmailVerifiedEvent(user_id="user-123", email="test@example.com")

        assert event.user_id == "user-123"
        assert event.email == "test@example.com"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserEmailVerifiedEvent(user_id="user-123", email="")
        assert event.event_type == "user.email_verified"


class TestUserLoggedInEvent:
    """Tests for UserLoggedInEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserLoggedInEvent(
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert event.user_id == "user-123"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserLoggedInEvent(user_id="user-123", ip_address="", user_agent="")
        assert event.event_type == "user.logged_in"


class TestUserReactivatedEvent:
    """Tests for UserReactivatedEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserReactivatedEvent(user_id="user-123")
        assert event.user_id == "user-123"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserReactivatedEvent(user_id="user-123")
        assert event.event_type == "user.reactivated"


class TestUserProfileUpdatedEvent:
    """Tests for UserProfileUpdatedEvent."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = UserProfileUpdatedEvent(
            user_id="user-123", changed_fields=("username", "display_name")
        )

        assert event.user_id == "user-123"
        assert "username" in event.changed_fields
        assert "display_name" in event.changed_fields

    def test_event_type(self) -> None:
        """Test event type property."""
        event = UserProfileUpdatedEvent(user_id="user-123", changed_fields=())
        assert event.event_type == "user.profile_updated"
