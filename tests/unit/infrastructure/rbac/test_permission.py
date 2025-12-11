"""Unit tests for RBAC permission module.

Tests Permission, PermissionSet, StandardResource, StandardAction,
and create_crud_permissions.
"""

import pytest

from infrastructure.rbac.permission import (
    Permission,
    PermissionSet,
    StandardAction,
    StandardResource,
    create_crud_permissions,
)


class TestStandardResource:
    """Tests for StandardResource enum."""

    def test_user_value(self) -> None:
        """Test USER value."""
        assert StandardResource.USER.value == "user"

    def test_role_value(self) -> None:
        """Test ROLE value."""
        assert StandardResource.ROLE.value == "role"

    def test_document_value(self) -> None:
        """Test DOCUMENT value."""
        assert StandardResource.DOCUMENT.value == "document"

    def test_all_values_are_strings(self) -> None:
        """Test all values are strings."""
        for resource in StandardResource:
            assert isinstance(resource.value, str)


class TestStandardAction:
    """Tests for StandardAction enum."""

    def test_create_value(self) -> None:
        """Test CREATE value."""
        assert StandardAction.CREATE.value == "create"

    def test_read_value(self) -> None:
        """Test READ value."""
        assert StandardAction.READ.value == "read"

    def test_update_value(self) -> None:
        """Test UPDATE value."""
        assert StandardAction.UPDATE.value == "update"

    def test_delete_value(self) -> None:
        """Test DELETE value."""
        assert StandardAction.DELETE.value == "delete"

    def test_list_value(self) -> None:
        """Test LIST value."""
        assert StandardAction.LIST.value == "list"


class TestPermission:
    """Tests for Permission dataclass."""

    def test_creation(self) -> None:
        """Test permission creation."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )

        assert perm.resource == StandardResource.USER
        assert perm.action == StandardAction.READ
        assert perm.conditions is None

    def test_str_representation(self) -> None:
        """Test string representation."""
        perm = Permission(
            resource=StandardResource.DOCUMENT,
            action=StandardAction.CREATE,
        )

        assert str(perm) == "document:create"

    def test_hash(self) -> None:
        """Test permission is hashable."""
        perm1 = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )
        perm2 = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )

        assert hash(perm1) == hash(perm2)

    def test_matches_true(self) -> None:
        """Test matches returns True for matching resource/action."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )

        assert perm.matches(StandardResource.USER, StandardAction.READ) is True

    def test_matches_false_resource(self) -> None:
        """Test matches returns False for different resource."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )

        assert perm.matches(StandardResource.ROLE, StandardAction.READ) is False

    def test_matches_false_action(self) -> None:
        """Test matches returns False for different action."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )

        assert perm.matches(StandardResource.USER, StandardAction.DELETE) is False

    def test_with_condition(self) -> None:
        """Test adding condition to permission."""
        perm = Permission(
            resource=StandardResource.DOCUMENT,
            action=StandardAction.READ,
        )

        perm_with_cond = perm.with_condition("own")

        assert perm_with_cond.conditions == frozenset({"own"})
        assert perm.conditions is None  # Original unchanged

    def test_with_multiple_conditions(self) -> None:
        """Test adding multiple conditions."""
        perm = Permission(
            resource=StandardResource.DOCUMENT,
            action=StandardAction.READ,
        )

        perm1 = perm.with_condition("own")
        perm2 = perm1.with_condition("department")

        assert perm2.conditions == frozenset({"own", "department"})

    def test_immutability(self) -> None:
        """Test permission is immutable."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )

        with pytest.raises(AttributeError):
            perm.resource = StandardResource.ROLE  # type: ignore[misc]


class TestPermissionSet:
    """Tests for PermissionSet class."""

    def test_empty_set(self) -> None:
        """Test empty permission set."""
        perm_set: PermissionSet[StandardResource, StandardAction] = PermissionSet()

        assert len(perm_set) == 0

    def test_add_permission(self) -> None:
        """Test adding permission."""
        perm_set: PermissionSet[StandardResource, StandardAction] = PermissionSet()
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )

        perm_set.add(perm)

        assert len(perm_set) == 1
        assert perm in perm_set

    def test_remove_permission(self) -> None:
        """Test removing permission."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )
        perm_set: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm})

        perm_set.remove(perm)

        assert len(perm_set) == 0

    def test_has_permission(self) -> None:
        """Test has method."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )
        perm_set: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm})

        assert perm_set.has(StandardResource.USER, StandardAction.READ) is True
        assert perm_set.has(StandardResource.USER, StandardAction.DELETE) is False

    def test_contains(self) -> None:
        """Test __contains__ method."""
        perm = Permission(
            resource=StandardResource.USER,
            action=StandardAction.READ,
        )
        perm_set: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm})

        assert perm in perm_set

    def test_iteration(self) -> None:
        """Test iteration over permissions."""
        perm1 = Permission(resource=StandardResource.USER, action=StandardAction.READ)
        perm2 = Permission(resource=StandardResource.ROLE, action=StandardAction.READ)
        perm_set: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm1, perm2})

        perms = list(perm_set)

        assert len(perms) == 2

    def test_union(self) -> None:
        """Test union of permission sets."""
        perm1 = Permission(resource=StandardResource.USER, action=StandardAction.READ)
        perm2 = Permission(resource=StandardResource.ROLE, action=StandardAction.READ)

        set1: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm1})
        set2: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm2})

        union = set1 | set2

        assert len(union) == 2
        assert perm1 in union
        assert perm2 in union

    def test_intersection(self) -> None:
        """Test intersection of permission sets."""
        perm1 = Permission(resource=StandardResource.USER, action=StandardAction.READ)
        perm2 = Permission(resource=StandardResource.ROLE, action=StandardAction.READ)

        set1: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm1, perm2})
        set2: PermissionSet[StandardResource, StandardAction] = PermissionSet({perm1})

        intersection = set1 & set2

        assert len(intersection) == 1
        assert perm1 in intersection


class TestCreateCrudPermissions:
    """Tests for create_crud_permissions factory."""

    def test_creates_five_permissions(self) -> None:
        """Test creates CRUD + list permissions."""
        perms = create_crud_permissions(StandardResource.USER)

        assert len(perms) == 5

    def test_has_create(self) -> None:
        """Test has CREATE permission."""
        perms = create_crud_permissions(StandardResource.USER)

        assert perms.has(StandardResource.USER, StandardAction.CREATE)

    def test_has_read(self) -> None:
        """Test has READ permission."""
        perms = create_crud_permissions(StandardResource.USER)

        assert perms.has(StandardResource.USER, StandardAction.READ)

    def test_has_update(self) -> None:
        """Test has UPDATE permission."""
        perms = create_crud_permissions(StandardResource.USER)

        assert perms.has(StandardResource.USER, StandardAction.UPDATE)

    def test_has_delete(self) -> None:
        """Test has DELETE permission."""
        perms = create_crud_permissions(StandardResource.USER)

        assert perms.has(StandardResource.USER, StandardAction.DELETE)

    def test_has_list(self) -> None:
        """Test has LIST permission."""
        perms = create_crud_permissions(StandardResource.USER)

        assert perms.has(StandardResource.USER, StandardAction.LIST)
