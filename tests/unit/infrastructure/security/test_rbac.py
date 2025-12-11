"""Unit tests for infrastructure/security/rbac.py.

Tests role-based access control.

**Task 21.3: Create tests for rbac.py**
**Requirements: 4.4**
"""

import pytest

from core.errors import AuthorizationError
from infrastructure.security.rbac import (
    ROLE_ADMIN,
    ROLE_USER,
    ROLE_VIEWER,
    Permission,
    RBACService,
    RBACUser,
    Role,
    get_rbac_service,
)


class TestPermission:
    """Tests for Permission enum."""

    def test_basic_permissions(self) -> None:
        """Test basic permission values."""
        assert Permission.READ.value == "read"
        assert Permission.WRITE.value == "write"
        assert Permission.DELETE.value == "delete"

    def test_admin_permissions(self) -> None:
        """Test admin permission values."""
        assert Permission.ADMIN.value == "admin"
        assert Permission.MANAGE_USERS.value == "manage_users"


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

    def test_has_permission(self) -> None:
        """Test has_permission method."""
        role = Role(
            name="test",
            permissions=frozenset([Permission.READ]),
        )

        assert role.has_permission(Permission.READ) is True
        assert role.has_permission(Permission.WRITE) is False

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        role = Role(
            name="test",
            permissions=frozenset([Permission.READ]),
            description="Test role",
        )

        result = role.to_dict()

        assert result["name"] == "test"
        assert "read" in result["permissions"]
        assert result["description"] == "Test role"

    def test_from_dict(self) -> None:
        """Test deserialization from dict."""
        data = {
            "name": "test",
            "permissions": ["read", "write"],
            "description": "Test role",
        }

        role = Role.from_dict(data)

        assert role.name == "test"
        assert Permission.READ in role.permissions
        assert Permission.WRITE in role.permissions

    def test_immutability(self) -> None:
        """Test role is immutable."""
        role = Role(name="test", permissions=frozenset([Permission.READ]))

        with pytest.raises(AttributeError):
            role.name = "new_name"


class TestPredefinedRoles:
    """Tests for predefined roles."""

    def test_admin_has_all_permissions(self) -> None:
        """Test admin role has all permissions."""
        for perm in Permission:
            assert ROLE_ADMIN.has_permission(perm) is True

    def test_user_has_read_write(self) -> None:
        """Test user role has read and write."""
        assert ROLE_USER.has_permission(Permission.READ) is True
        assert ROLE_USER.has_permission(Permission.WRITE) is True
        assert ROLE_USER.has_permission(Permission.DELETE) is False

    def test_viewer_has_read_only(self) -> None:
        """Test viewer role has read only."""
        assert ROLE_VIEWER.has_permission(Permission.READ) is True
        assert ROLE_VIEWER.has_permission(Permission.WRITE) is False


class TestRBACUser:
    """Tests for RBACUser dataclass."""

    def test_create_user(self) -> None:
        """Test creating RBAC user."""
        user = RBACUser(id="user-123", roles=["admin", "user"])

        assert user.id == "user-123"
        assert "admin" in user.roles

    def test_user_with_scopes(self) -> None:
        """Test user with OAuth scopes."""
        user = RBACUser(id="user-123", roles=["user"], scopes=["read", "write"])

        assert "read" in user.scopes


class TestRBACService:
    """Tests for RBACService."""

    def test_get_role(self) -> None:
        """Test getting role by name."""
        service = RBACService()

        role = service.get_role("admin")

        assert role is not None
        assert role.name == "admin"

    def test_get_nonexistent_role(self) -> None:
        """Test getting nonexistent role returns None."""
        service = RBACService()

        role = service.get_role("nonexistent")

        assert role is None

    def test_add_role(self) -> None:
        """Test adding custom role."""
        service = RBACService()
        custom_role = Role(
            name="custom",
            permissions=frozenset([Permission.READ]),
        )

        service.add_role(custom_role)

        assert service.get_role("custom") is not None

    def test_get_user_permissions(self) -> None:
        """Test getting all user permissions."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])

        permissions = service.get_user_permissions(user)

        assert Permission.READ in permissions
        assert Permission.WRITE in permissions

    def test_get_user_permissions_multiple_roles(self) -> None:
        """Test permissions from multiple roles are combined."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer", "moderator"])

        permissions = service.get_user_permissions(user)

        assert Permission.READ in permissions
        assert Permission.DELETE in permissions
        assert Permission.VIEW_AUDIT in permissions

    def test_check_permission_granted(self) -> None:
        """Test check_permission returns True when granted."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])

        result = service.check_permission(user, Permission.READ)

        assert result is True

    def test_check_permission_denied(self) -> None:
        """Test check_permission returns False when denied."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])

        result = service.check_permission(user, Permission.WRITE)

        assert result is False

    def test_check_any_permission(self) -> None:
        """Test check_any_permission with multiple options."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])

        result = service.check_any_permission(user, [Permission.WRITE, Permission.READ])

        assert result is True

    def test_check_all_permissions(self) -> None:
        """Test check_all_permissions requires all."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])

        result = service.check_all_permissions(user, [Permission.READ, Permission.WRITE])

        assert result is True

    def test_check_all_permissions_missing_one(self) -> None:
        """Test check_all_permissions fails if one missing."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])

        result = service.check_all_permissions(user, [Permission.READ, Permission.WRITE])

        assert result is False

    def test_require_permission_granted(self) -> None:
        """Test require_permission passes when granted."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["user"])

        # Should not raise
        service.require_permission(user, Permission.READ)

    def test_require_permission_denied(self) -> None:
        """Test require_permission raises when denied."""
        service = RBACService()
        user = RBACUser(id="user-123", roles=["viewer"])

        with pytest.raises(AuthorizationError):
            service.require_permission(user, Permission.WRITE)


class TestGetRBACService:
    """Tests for get_rbac_service function."""

    def test_returns_service(self) -> None:
        """Test get_rbac_service returns RBACService."""
        service = get_rbac_service()

        assert isinstance(service, RBACService)

    def test_returns_same_instance(self) -> None:
        """Test get_rbac_service returns singleton."""
        service1 = get_rbac_service()
        service2 = get_rbac_service()

        assert service1 is service2
