"""Tests for read models module.

**Feature: realistic-test-coverage**
**Validates: Requirements 4.3, 6.1**
"""

from datetime import UTC, datetime

import pytest

from infrastructure.db.models.read_models import UserReadModel


class TestUserReadModel:
    """Tests for UserReadModel."""

    def test_create_model(self) -> None:
        """Test creating a user read model."""
        now = datetime.now(UTC)
        model = UserReadModel(
            id="user-123",
            email="test@example.com",
            username="testuser",
            display_name="Test User",
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        assert model.id == "user-123"
        assert model.email == "test@example.com"
        assert model.username == "testuser"

    def test_explicit_values(self) -> None:
        """Test explicit boolean values."""
        now = datetime.now(UTC)
        model = UserReadModel(
            id="user-123",
            email="test@example.com",
            created_at=now,
            updated_at=now,
            is_active=True,
            is_verified=False,
            permission_count=0,
        )
        assert model.is_active is True
        assert model.is_verified is False
        assert model.permission_count == 0

    def test_to_dict(self) -> None:
        """Test converting model to dictionary."""
        now = datetime.now(UTC)
        model = UserReadModel(
            id="user-123",
            email="test@example.com",
            username="testuser",
            display_name="Test User",
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
            role_names="admin,user",
            permission_count=5,
        )
        result = model.to_dict()
        
        assert result["id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert result["display_name"] == "Test User"
        assert result["is_active"] is True
        assert result["is_verified"] is True
        assert result["role_names"] == ["admin", "user"]
        assert result["permission_count"] == 5

    def test_to_dict_empty_roles(self) -> None:
        """Test to_dict with no roles."""
        now = datetime.now(UTC)
        model = UserReadModel(
            id="user-123",
            email="test@example.com",
            created_at=now,
            updated_at=now,
            role_names=None,
        )
        result = model.to_dict()
        assert result["role_names"] == []

    def test_to_dict_with_last_login(self) -> None:
        """Test to_dict includes last_login_at."""
        now = datetime.now(UTC)
        model = UserReadModel(
            id="user-123",
            email="test@example.com",
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )
        result = model.to_dict()
        assert result["last_login_at"] is not None

    def test_to_dict_without_last_login(self) -> None:
        """Test to_dict with no last_login_at."""
        now = datetime.now(UTC)
        model = UserReadModel(
            id="user-123",
            email="test@example.com",
            created_at=now,
            updated_at=now,
            last_login_at=None,
        )
        result = model.to_dict()
        assert result["last_login_at"] is None

    def test_from_dict(self) -> None:
        """Test creating model from dictionary."""
        now = datetime.now(UTC)
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "username": "testuser",
            "display_name": "Test User",
            "is_active": True,
            "is_verified": True,
            "created_at": now,
            "updated_at": now,
            "role_names": ["admin", "user"],
            "permission_count": 5,
        }
        model = UserReadModel.from_dict(data)
        
        assert model.id == "user-123"
        assert model.email == "test@example.com"
        assert model.role_names == "admin,user"

    def test_from_dict_with_string_roles(self) -> None:
        """Test from_dict with string role_names."""
        now = datetime.now(UTC)
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "created_at": now,
            "updated_at": now,
            "role_names": "admin,user",
        }
        model = UserReadModel.from_dict(data)
        assert model.role_names == "admin,user"

    def test_from_dict_defaults(self) -> None:
        """Test from_dict with default values."""
        now = datetime.now(UTC)
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "created_at": now,
            "updated_at": now,
        }
        model = UserReadModel.from_dict(data)
        
        assert model.is_active is True
        assert model.is_verified is False
        assert model.permission_count == 0

    def test_from_dict_with_deactivation_reason(self) -> None:
        """Test from_dict with deactivation reason."""
        now = datetime.now(UTC)
        data = {
            "id": "user-123",
            "email": "test@example.com",
            "created_at": now,
            "updated_at": now,
            "is_active": False,
            "deactivation_reason": "User requested account deletion",
        }
        model = UserReadModel.from_dict(data)
        assert model.deactivation_reason == "User requested account deletion"

    def test_tablename(self) -> None:
        """Test table name is correct."""
        assert UserReadModel.__tablename__ == "users_read"
