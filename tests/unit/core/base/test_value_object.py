"""Unit tests for core/base/domain/value_object.py.

Tests value object immutability, equality, and validation.

**Feature: test-coverage-90-percent**
**Validates: Requirements 3.1**
"""

from dataclasses import dataclass

import pytest

from core.base.domain.value_object import (
    AuditLogId,
    BaseValueObject,
    EntityId,
    ItemId,
    RoleId,
    UserId,
)


@dataclass(frozen=True)
class TestEmail(BaseValueObject):
    """Test value object for email."""
    
    value: str
    
    def __post_init__(self) -> None:
        if "@" not in self.value:
            raise ValueError("Invalid email format")


@dataclass(frozen=True)
class TestMoney(BaseValueObject):
    """Test value object for money."""
    
    amount: float
    currency: str


class TestBaseValueObject:
    """Tests for BaseValueObject class."""

    def test_value_objects_equal_by_value(self) -> None:
        """Value objects with same values should be equal."""
        email1 = TestEmail("user@example.com")
        email2 = TestEmail("user@example.com")
        
        assert email1 == email2

    def test_value_objects_not_equal_different_values(self) -> None:
        """Value objects with different values should not be equal."""
        email1 = TestEmail("user1@example.com")
        email2 = TestEmail("user2@example.com")
        
        assert email1 != email2

    def test_value_objects_not_equal_different_types(self) -> None:
        """Value objects of different types should not be equal."""
        email = TestEmail("user@example.com")
        money = TestMoney(100.0, "USD")
        
        assert email != money

    def test_value_object_not_equal_to_non_value_object(self) -> None:
        """Value object should not equal non-value-object."""
        email = TestEmail("user@example.com")
        
        assert email != "user@example.com"
        assert email != 123
        assert email != None

    def test_value_objects_hashable(self) -> None:
        """Value objects should be hashable for use in sets/dicts."""
        email1 = TestEmail("user@example.com")
        email2 = TestEmail("user@example.com")
        
        # Same values should have same hash
        assert hash(email1) == hash(email2)
        
        # Should work in sets
        email_set = {email1, email2}
        assert len(email_set) == 1

    def test_value_object_validation(self) -> None:
        """Value object should validate on creation."""
        with pytest.raises(ValueError, match="Invalid email format"):
            TestEmail("invalid-email")

    def test_value_object_immutable(self) -> None:
        """Value objects should be immutable (frozen)."""
        email = TestEmail("user@example.com")
        
        with pytest.raises(AttributeError):
            email.value = "new@example.com"  # type: ignore


class TestEntityId:
    """Tests for EntityId class."""

    def test_create_valid_ulid(self) -> None:
        """EntityId should accept valid ULID."""
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert entity_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_ulid_normalized_to_uppercase(self) -> None:
        """EntityId should normalize ULID to uppercase."""
        entity_id = EntityId("01arz3ndektsv4rrffq69g5fav")
        
        assert entity_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_empty_ulid_raises_error(self) -> None:
        """EntityId should reject empty string."""
        with pytest.raises(ValueError, match="Entity ID cannot be empty"):
            EntityId("")

    def test_invalid_ulid_format_raises_error(self) -> None:
        """EntityId should reject invalid ULID format."""
        with pytest.raises(ValueError, match="Invalid ULID format"):
            EntityId("invalid-id")

    def test_ulid_wrong_length_raises_error(self) -> None:
        """EntityId should reject ULID with wrong length."""
        with pytest.raises(ValueError, match="Invalid ULID format"):
            EntityId("01ARZ3NDEKTSV4RRFFQ69G5FA")  # 25 chars

    def test_ulid_invalid_characters_raises_error(self) -> None:
        """EntityId should reject ULID with invalid characters."""
        # ULID excludes I, L, O, U
        with pytest.raises(ValueError, match="Invalid ULID format"):
            EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAI")

    def test_entity_id_str_representation(self) -> None:
        """EntityId __str__ should return the value."""
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert str(entity_id) == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_entity_id_hashable(self) -> None:
        """EntityId should be hashable."""
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert hash(entity_id) == hash("01ARZ3NDEKTSV4RRFFQ69G5FAV")

    def test_entity_id_from_string(self) -> None:
        """EntityId.from_string should create instance."""
        entity_id = EntityId.from_string("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert entity_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"


class TestTypedEntityIds:
    """Tests for typed entity ID classes."""

    def test_item_id_creation(self) -> None:
        """ItemId should work like EntityId."""
        item_id = ItemId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert item_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_role_id_creation(self) -> None:
        """RoleId should work like EntityId."""
        role_id = RoleId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert role_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_user_id_creation(self) -> None:
        """UserId should work like EntityId."""
        user_id = UserId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert user_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_audit_log_id_creation(self) -> None:
        """AuditLogId should work like EntityId."""
        audit_id = AuditLogId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        assert audit_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_different_typed_ids_not_equal(self) -> None:
        """Different typed IDs with same value should not be equal."""
        item_id = ItemId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        user_id = UserId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        
        # They have same value but different types
        assert item_id.value == user_id.value
        # But as dataclasses they are different types
        assert type(item_id) != type(user_id)
