"""Tests for user domain events.

Tests UserRegisteredEvent, UserDeactivatedEvent, and other user events.
"""

import pytest

from domain.users.events import (
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

    def test_create_event(self) -> None:
        event = UserRegisteredEvent(user_id="user-123", email="user@example.com")
        assert event.user_id == "user-123"
        assert event.email == "user@example.com"

    def test_event_type(self) -> None:
        event = UserRegisteredEvent(user_id="user-123", email="user@example.com")
        assert event.event_type == "user.registered"

    def test_is_frozen(self) -> None:
        event = UserRegisteredEvent(user_id="user-123", email="user@example.com")
        with pytest.raises(AttributeError):
            event.user_id = "changed"  # type: ignore

    def test_default_values(self) -> None:
        event = UserRegisteredEvent()
        assert event.user_id == ""
        assert event.email == ""


class TestUserDeactivatedEvent:
    """Tests for UserDeactivatedEvent."""

    def test_create_event(self) -> None:
        event = UserDeactivatedEvent(user_id="user-123", reason="Inactive")
        assert event.user_id == "user-123"
        assert event.reason == "Inactive"

    def test_event_type(self) -> None:
        event = UserDeactivatedEvent(user_id="user-123", reason="Inactive")
        assert event.event_type == "user.deactivated"

    def test_default_values(self) -> None:
        event = UserDeactivatedEvent()
        assert event.user_id == ""
        assert event.reason == ""


class TestUserEmailChangedEvent:
    """Tests for UserEmailChangedEvent."""

    def test_create_event(self) -> None:
        event = UserEmailChangedEvent(
            user_id="user-123",
            old_email="old@example.com",
            new_email="new@example.com",
        )
        assert event.user_id == "user-123"
        assert event.old_email == "old@example.com"
        assert event.new_email == "new@example.com"

    def test_event_type(self) -> None:
        event = UserEmailChangedEvent(
            user_id="user-123",
            old_email="old@example.com",
            new_email="new@example.com",
        )
        assert event.event_type == "user.email_changed"


class TestUserPasswordChangedEvent:
    """Tests for UserPasswordChangedEvent."""

    def test_create_event(self) -> None:
        event = UserPasswordChangedEvent(user_id="user-123")
        assert event.user_id == "user-123"

    def test_event_type(self) -> None:
        event = UserPasswordChangedEvent(user_id="user-123")
        assert event.event_type == "user.password_changed"


class TestUserEmailVerifiedEvent:
    """Tests for UserEmailVerifiedEvent."""

    def test_create_event(self) -> None:
        event = UserEmailVerifiedEvent(user_id="user-123", email="user@example.com")
        assert event.user_id == "user-123"
        assert event.email == "user@example.com"

    def test_event_type(self) -> None:
        event = UserEmailVerifiedEvent(user_id="user-123", email="user@example.com")
        assert event.event_type == "user.email_verified"


class TestUserLoggedInEvent:
    """Tests for UserLoggedInEvent."""

    def test_create_event(self) -> None:
        event = UserLoggedInEvent(
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert event.user_id == "user-123"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"

    def test_event_type(self) -> None:
        event = UserLoggedInEvent(
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert event.event_type == "user.logged_in"

    def test_default_values(self) -> None:
        event = UserLoggedInEvent()
        assert event.user_id == ""
        assert event.ip_address == ""
        assert event.user_agent == ""


class TestUserReactivatedEvent:
    """Tests for UserReactivatedEvent."""

    def test_create_event(self) -> None:
        event = UserReactivatedEvent(user_id="user-123")
        assert event.user_id == "user-123"

    def test_event_type(self) -> None:
        event = UserReactivatedEvent(user_id="user-123")
        assert event.event_type == "user.reactivated"


class TestUserProfileUpdatedEvent:
    """Tests for UserProfileUpdatedEvent."""

    def test_create_event(self) -> None:
        event = UserProfileUpdatedEvent(
            user_id="user-123",
            changed_fields=("name", "bio"),
        )
        assert event.user_id == "user-123"
        assert event.changed_fields == ("name", "bio")

    def test_event_type(self) -> None:
        event = UserProfileUpdatedEvent(user_id="user-123")
        assert event.event_type == "user.profile_updated"

    def test_default_changed_fields(self) -> None:
        event = UserProfileUpdatedEvent(user_id="user-123")
        assert event.changed_fields == ()
