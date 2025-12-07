"""Tests for RBAC module.

**Feature: realistic-test-coverage**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

import pytest

from core.errors import AuthorizationError
from infrastructure.security.rbac import (
    Permission,
    RBACService,
    RBACUser,
    Role,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_USER,
    ROLE_VIEWER,
    get_rbac_service,
)


class TestPermission:
    """Tests for Permission enum."""

    def test_read_value(self) -> None:
        """Test READ permission value."""
        assert Permission.READ.value == "read"

    def test_write_value(self) -> None:
        """Test WRITE permission value."""
        assert Permission.WRITE.value == "write"

    def test_delete_value(self) -> None:
        """Test DELETE permission value."""
        assert Permission.DELETE.value == "delete"

    def test_admin_value(self) -> None:
        """Test ADMIN permission value."""
        assert Permission.ADMIN.value == "admin"

    def test_is_string_enum(self) -> None:
        """Test Permission is a string enum."""
        assert isinstance(Permission.READ, str)


class TestRole:
    """Tests for Role dataclass."""

    def test_create_role(self) -> None:
        """Test creating a role."""
        role = Role(
            name="custom",
            permissions=frozenset([Permission.READ, Permission.WRITE]),
            description="Custom role",
        )
        assert role.name == "custom"
        assert Permission.READ in role.permissions

    def test_has_permission_true(self) -> None:
        """Test has_permission returns True."""
        role = Role(
            name="test",
            permissions=frozenset([Permission.READ]),
        )
        assert role.has_permission(Permission.READ) is True

    def test_has_permission_false(self) -> None:
        """Test has_permission returns False."""
        role = Role(
            name="test",
            permissions=frozenset([Permission.READ]),
        )
        assert role.has_permission(Permission.WRITE) is False

    def test_to_dict(self) -> None:
        """Test converting role to dictionary."""
        role = Role(
            name="test",
            permissions=frozenset([Permission.READ, Permission.WRITE]),
            description="Test role",
        )
        data = role.to_dict()
        
        assert data["name"] == "test"
        assert "read" in data["permissions"]
        assert "write" in data["permissions"]
        assert data["description"] == "Test role"

    def test_from_dict(self) -> None:
        """Test creating role from dictionary."""
        data = {
            "name": "test",
            "permissions": ["read", "write"],
            "description": "Test role",
        }
        role = Role.from_dict(data)
        
        assert role.name == "test"
        assert Permission.READ in role.permissions
        assert role.description == "Test role"

    def test_from_dict_defaults(self) -> None:
        """Test from_dict with defaults."""
        data = {"name": "test"}
        role = Role.from_dict(data)
        
        assert role.permissions == frozenset()
        assert role.description == ""

    def test_is_frozen(self) -> None:
        """Test role is immutable."""
        role = Role(name="test")
        with pytest.raises(AttributeError):
            role.name = "new"


class TestPredefinedRoles:
    """Tests for predefined roles."""

    def test_admin_has_all_permissions(self) -> None:
        """Test admin role has all permissions."""
        for perm in Permission:
            assert ROLE_ADMIN.has_permission(perm)

    def test_user_has_read_write(self) -> None:
        """Test user role has read and write."""
        assert ROLE_USER.has_permission(Permission.READ)
        assert ROLE_USER.has_permission(Permission.WRITE)
        assert not ROLE_USER.has_permission(Permission.DELETE)

    def test_viewer_has_read_only(self) -> None:
        """Test viewer role has read only."""
        assert ROLE_VIEWER.has_permission(Permission.READ)
        assert not ROLE_VIEWER.has_permission(Permission.WRITE)

    def test_moderator_permissions(self) -> None:
        """Test moderator role permissions."""
        assert ROLE_MODERATOR.has_permission(Permission.READ)
        assert ROLE_MODERATOR.has_permission(Permission.WRITE)
        assert ROLE_MODERATOR.has_permission(Permission.DELETE)
        assert ROLE_MODERATOR.has_permission(Permission.VIEW_AUDIT)


class TestRBACUser:
    """Tests for RBACUser."""

    def test_create_user(self) -> None:
        """Test creating RBAC user."""
        user = RBACUser(id="user-123", roles=["admin"])
        assert user.id == "user-123"
        assert "admin" in user.roles

    def test_default_roles(self) -> None:
        """Test default roles is empty."""
        user = RBACUser(id="user-123")
        assert user.roles == []

    def test_default_scopes(self) -> None:
        """Test default scopes is empty."""
        user = RBACUser(id="user-123")
        assert user.scopes == []


class TestRBACService:
    """Tests for RBACService."""

    def test_get_role(self) -> None:
        """Test getting a role."""
        service = RBACService()
        role = service.get_role("admin")
        assert role is not None
        assert role.name == "admin"

    def test_get_role_not_found(self) -> None:
        """Test getting non-existent role."""
        service = RBACService()
        role = service.get_role("non-existent")
        assert role is None

    def test_add_role(self) -> None:
        """Test adding a role."""
        service = RBACService()
        custom_role = Role(
            name="custom",
            permissions=frozenset([Permission.READ]),
        )
        service.add_role(custom_role)
        
        role = service.get_role("custom")
        assert role is not None
        assert role.name == "custom"

    def test_get_user_permissions(self) -> None:
        """Test getting user permissions."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])
        
        permissions = service.get_user_permissions(user)
        
        assert Permission.READ in permissions
        assert Permission.WRITE in permissions

    def test_get_user_permissions_multiple_roles(self) -> None:
        """Test permissions from multiple roles."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer", "moderator"])
        
        permissions = service.get_user_permissions(user)
        
        assert Permission.READ in permissions
        assert Permission.DELETE in permissions
        assert Permission.VIEW_AUDIT in permissions

    def test_get_user_permissions_with_scopes(self) -> None:
        """Test permissions include scopes."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=[], scopes=["read"])
        
        permissions = service.get_user_permissions(user)
        
        assert Permission.READ in permissions

    def test_check_permission_true(self) -> None:
        """Test check_permission returns True."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])
        
        assert service.check_permission(user, Permission.READ) is True

    def test_check_permission_false(self) -> None:
        """Test check_permission returns False."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])
        
        assert service.check_permission(user, Permission.WRITE) is False

    def test_check_any_permission_true(self) -> None:
        """Test check_any_permission returns True."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])
        
        result = service.check_any_permission(
            user, [Permission.READ, Permission.WRITE]
        )
        assert result is True

    def test_check_any_permission_false(self) -> None:
        """Test check_any_permission returns False."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])
        
        result = service.check_any_permission(
            user, [Permission.WRITE, Permission.DELETE]
        )
        assert result is False

    def test_check_all_permissions_true(self) -> None:
        """Test check_all_permissions returns True."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])
        
        result = service.check_all_permissions(
            user, [Permission.READ, Permission.WRITE]
        )
        assert result is True

    def test_check_all_permissions_false(self) -> None:
        """Test check_all_permissions returns False."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])
        
        result = service.check_all_permissions(
            user, [Permission.READ, Permission.DELETE]
        )
        assert result is False

    def test_require_permission_success(self) -> None:
        """Test require_permission succeeds."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])
        
        # Should not raise
        service.require_permission(user, Permission.READ)

    def test_require_permission_failure(self) -> None:
        """Test require_permission raises error."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])
        
        with pytest.raises(AuthorizationError):
            service.require_permission(user, Permission.WRITE)


class TestGetRbacService:
    """Tests for get_rbac_service function."""

    def test_returns_service(self) -> None:
        """Test returns RBACService instance."""
        service = get_rbac_service()
        assert isinstance(service, RBACService)

    def test_returns_same_instance(self) -> None:
        """Test returns same instance (singleton)."""
        service1 = get_rbac_service()
        service2 = get_rbac_service()
        assert service1 is service2
