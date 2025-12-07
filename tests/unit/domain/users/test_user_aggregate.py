"""Unit tests for UserAggregate.

Tests user creation, email change, password change, deactivation, and events.
"""

from datetime import UTC, datetime

import pytest

from domain.users.aggregates.aggregates import UserAggregate
from domain.users.events import (
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

    def test_create_with_username(self) -> None:
        """Test creating user with username."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
            username="testuser",
        )
        
        assert user.username == "testuser"

    def test_create_with_display_name(self) -> None:
        """Test creating user with display name."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
            display_name="Test User",
        )
        
        assert user.display_name == "Test User"

    def test_create_emits_registered_event(self) -> None:
        """Test that create emits UserRegisteredEvent."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        
        events = user.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], UserRegisteredEvent)
        assert events[0].user_id == "user-123"
        assert events[0].email == "test@example.com"

    def test_create_with_invalid_email_raises(self) -> None:
        """Test that invalid email raises error."""
        with pytest.raises(ValueError):
            UserAggregate.create(
                user_id="user-123",
                email="invalid-email",
                password_hash="hashed",
            )


class TestUserAggregateChangeEmail:
    """Tests for UserAggregate.change_email method."""

    def test_change_email(self) -> None:
        """Test changing email."""
        user = UserAggregate.create(
            user_id="user-123",
            email="old@example.com",
            password_hash="hashed",
        )
        user.clear_events()
        
        user.change_email("new@example.com")
        
        assert user.email == "new@example.com"

    def test_change_email_resets_verification(self) -> None:
        """Test that changing email resets verification."""
        user = UserAggregate.create(
            user_id="user-123",
            email="old@example.com",
            password_hash="hashed",
        )
        user.verify_email()
        assert user.is_verified is True
        
        user.change_email("new@example.com")
        
        assert user.is_verified is False

    def test_change_email_emits_event(self) -> None:
        """Test that change_email emits event."""
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


class TestUserAggregatePassword:
    """Tests for UserAggregate password methods."""

    def test_change_password(self) -> None:
        """Test changing password."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="old_hash",
        )
        
        user.change_password("new_hash")
        
        assert user.password_hash == "new_hash"


class TestUserAggregateVerification:
    """Tests for UserAggregate verification methods."""

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


class TestUserAggregateActivation:
    """Tests for UserAggregate activation methods."""

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
        """Test that deactivate emits event."""
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


class TestUserAggregateLogin:
    """Tests for UserAggregate login methods."""

    def test_record_login(self) -> None:
        """Test recording login."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        assert user.last_login_at is None
        
        login_time = datetime.now(UTC)
        user.record_login(login_time)
        
        assert user.last_login_at == login_time


class TestUserAggregateProfile:
    """Tests for UserAggregate profile methods."""

    def test_update_profile_username(self) -> None:
        """Test updating username."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        
        user.update_profile(username="newuser")
        
        assert user.username == "newuser"

    def test_update_profile_display_name(self) -> None:
        """Test updating display name."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        
        user.update_profile(display_name="New Name")
        
        assert user.display_name == "New Name"

    def test_update_profile_both(self) -> None:
        """Test updating both username and display name."""
        user = UserAggregate.create(
            user_id="user-123",
            email="test@example.com",
            password_hash="hashed",
        )
        
        user.update_profile(username="newuser", display_name="New Name")
        
        assert user.username == "newuser"
        assert user.display_name == "New Name"
