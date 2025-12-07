"""Tests for RBAC models module.

**Feature: realistic-test-coverage**
**Validates: Requirements for core-rbac-system**
"""

from datetime import UTC, datetime

import pytest

from infrastructure.db.models.rbac_models import RoleModel, UserRoleModel


class TestRoleModel:
    """Tests for RoleModel."""

    def test_create_role(self) -> None:
        """Test creating a role model."""
        now = datetime.now(UTC)
        role = RoleModel(
            id="role-123",
            name="admin",
            description="Administrator role",
            permissions=["read", "write", "delete"],
            is_system=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert role.id == "role-123"
        assert role.name == "admin"
        assert role.permissions == ["read", "write", "delete"]

    def test_explicit_values(self) -> None:
        """Test explicit boolean values."""
        now = datetime.now(UTC)
        role = RoleModel(
            id="role-123",
            name="user",
            created_at=now,
            updated_at=now,
            is_system=False,
            is_active=True,
            permissions=[],
        )
        assert role.is_system is False
        assert role.is_active is True

    def test_to_dict(self) -> None:
        """Test converting role to dictionary."""
        now = datetime.now(UTC)
        role = RoleModel(
            id="role-123",
            name="admin",
            description="Administrator role",
            permissions=["read", "write"],
            is_system=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        result = role.to_dict()
        
        assert result["id"] == "role-123"
        assert result["name"] == "admin"
        assert result["description"] == "Administrator role"
        assert result["permissions"] == ["read", "write"]
        assert result["is_system"] is True
        assert result["is_active"] is True
        assert result["created_at"] is not None
        assert result["updated_at"] is not None

    def test_to_dict_without_timestamps(self) -> None:
        """Test to_dict handles None timestamps."""
        role = RoleModel(
            id="role-123",
            name="admin",
            permissions=[],
        )
        role.created_at = None
        role.updated_at = None
        result = role.to_dict()
        
        assert result["created_at"] is None
        assert result["updated_at"] is None

    def test_tablename(self) -> None:
        """Test table name is correct."""
        assert RoleModel.__tablename__ == "roles"

    def test_empty_permissions(self) -> None:
        """Test role with empty permissions."""
        now = datetime.now(UTC)
        role = RoleModel(
            id="role-123",
            name="guest",
            permissions=[],
            created_at=now,
            updated_at=now,
        )
        assert role.permissions == []


class TestUserRoleModel:
    """Tests for UserRoleModel."""

    def test_create_user_role(self) -> None:
        """Test creating a user role mapping."""
        now = datetime.now(UTC)
        user_role = UserRoleModel(
            id="ur-123",
            user_id="user-456",
            role_id="role-789",
            assigned_at=now,
            assigned_by="admin-001",
        )
        assert user_role.id == "ur-123"
        assert user_role.user_id == "user-456"
        assert user_role.role_id == "role-789"
        assert user_role.assigned_by == "admin-001"

    def test_to_dict(self) -> None:
        """Test converting user role to dictionary."""
        now = datetime.now(UTC)
        user_role = UserRoleModel(
            id="ur-123",
            user_id="user-456",
            role_id="role-789",
            assigned_at=now,
            assigned_by="admin-001",
        )
        result = user_role.to_dict()
        
        assert result["id"] == "ur-123"
        assert result["user_id"] == "user-456"
        assert result["role_id"] == "role-789"
        assert result["assigned_at"] is not None
        assert result["assigned_by"] == "admin-001"

    def test_to_dict_without_assigned_by(self) -> None:
        """Test to_dict with no assigned_by."""
        now = datetime.now(UTC)
        user_role = UserRoleModel(
            id="ur-123",
            user_id="user-456",
            role_id="role-789",
            assigned_at=now,
            assigned_by=None,
        )
        result = user_role.to_dict()
        assert result["assigned_by"] is None

    def test_to_dict_without_timestamp(self) -> None:
        """Test to_dict handles None assigned_at."""
        user_role = UserRoleModel(
            id="ur-123",
            user_id="user-456",
            role_id="role-789",
        )
        user_role.assigned_at = None
        result = user_role.to_dict()
        assert result["assigned_at"] is None

    def test_tablename(self) -> None:
        """Test table name is correct."""
        assert UserRoleModel.__tablename__ == "user_roles"
