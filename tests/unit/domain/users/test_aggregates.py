"""Unit tests for domain/users/aggregates/aggregates.py.

Tests User aggregate creation and behavior.

**Task 8.1: Create tests for User aggregate**
**Requirements: 2.2**
"""

from datetime import datetime, UTC

import pytest

from domain.users.aggregates.aggregates import UserAggregate
from domain.users.events.events import (
    UserDeactivatedEvent,
    UserEmailChangedEvent,
    UserRegisteredEvent,
)


class TestUserAggregateCreate:
    """Tests for UserAggregate.create factory method."""

    def test_create_user(self) -> None:
        """Test creating a new user."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed_password",
        )

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.is_active is True
        assert user.is_verified is False

    def test_create_user_with_optional_fields(self) -> None:
        """Test creating user with optional fields."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed_password",
            username="testuser",
            display_name="Test User",
        )

        assert user.username == "testuser"
        assert user.display_name == "Test User"

    def test_create_emits_registered_event(self) -> None:
        """Test create emits UserRegisteredEvent."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed_password",
        )

        events = user.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], UserRegisteredEvent)
        assert events[0].user_id == "user-123"
        assert events[0].email == "test@example.com"

    def test_create_normalizes_email(self) -> None:
        """Test email is normalized to lowercase."""
        user = UserAggregate.create(
            user_id="user-123",
            email="Test@Example.COM",
            password_hash="hashed_password",
        )

        assert user.email == "test@example.com"

    def test_create_invalid_email_raises(self) -> None:
        """Test invalid email raises ValueError."""
        with pytest.raises(ValueError):
            UserAggregate.create(
                user_id="user-123",
                email="invalid-email",
                password_hash="hashed_password",
            )


class TestUserAggregateChangeEmail:
    """Tests for UserAggregate.change_email method."""

    def test_change_email(self) -> None:
        """Test changing user email."""
        user = UserAggregate.create(
            user_id="user-123",
            email="old@example.com",
            password_hash="hashed",
        )
        user.clear_events()

        user.change_email("new@example.com")

        assert user.email == "new@example.com"
        assert user.is_verified is False

    def test_change_email_emits_event(self) -> None:
        """Test change_email emits UserEmailChangedEvent."""
        user = UserAggregate.create(
            user_id="user-123",
            email="old@example.com",
            password_hash="hashed",
        )
        user.clear_events()

        user.change_email("new@example.com")

        events = user.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], UserEmailChangedEvent)
        assert events[0].old_email == "old@example.com"
        assert events[0].new_email == "new@example.com"

    def test_change_email_increments_version(self) -> None:
        """Test change_email increments version."""
        user = UserAggregate.create(
            user_id="user-123",
            email="old@example.com",
            password_hash="hashed",
        )
        initial_version = user.version

        user.change_email("new@example.com")

        assert user.version == initial_version + 1


class TestUserAggregateDeactivate:
    """Tests for UserAggregate.deactivate method."""

    def test_deactivate(self) -> None:
        """Test deactivating user."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        user.clear_events()

        user.deactivate(reason="User requested")

        assert user.is_active is False

    def test_deactivate_emits_event(self) -> None:
        """Test deactivate emits UserDeactivatedEvent."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        user.clear_events()

        user.deactivate(reason="Violation")

        events = user.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], UserDeactivatedEvent)
        assert events[0].reason == "Violation"


class TestUserAggregateOtherMethods:
    """Tests for other UserAggregate methods."""

    def test_change_password(self) -> None:
        """Test changing password."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="old_hash",
        )

        user.change_password("new_hash")

        assert user.password_hash == "new_hash"

    def test_verify_email(self) -> None:
        """Test verifying email."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        assert user.is_verified is False

        user.verify_email()

        assert user.is_verified is True

    def test_reactivate(self) -> None:
        """Test reactivating user."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        user.deactivate()
        assert user.is_active is False

        user.reactivate()

        assert user.is_active is True

    def test_record_login(self) -> None:
        """Test recording login."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        login_time = datetime.now(UTC)

        user.record_login(login_time)

        assert user.last_login_at == login_time

    def test_update_profile(self) -> None:
        """Test updating profile."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )

        user.update_profile(username="newuser", display_name="New Name")

        assert user.username == "newuser"
        assert user.display_name == "New Name"
