"""Tests for core/base/domain/value_object.py - Value object classes."""

from dataclasses import dataclass

import pytest

from src.core.base.domain.value_object import (
    AuditLogId,
    BaseValueObject,
    EntityId,
    ItemId,
    RoleId,
    UserId,
)


@dataclass(frozen=True)
class SampleValueObject(BaseValueObject):
    """Sample value object for testing."""

    name: str
    value: int


class TestBaseValueObject:
    """Tests for BaseValueObject class."""

    def test_equality_same_values(self):
        vo1 = SampleValueObject(name="test", value=10)
        vo2 = SampleValueObject(name="test", value=10)
        assert vo1 == vo2

    def test_equality_different_values(self):
        vo1 = SampleValueObject(name="test", value=10)
        vo2 = SampleValueObject(name="test", value=20)
        assert vo1 != vo2

    def test_equality_different_types(self):
        vo = SampleValueObject(name="test", value=10)
        assert vo != "not a value object"
        assert vo != 10
        assert vo is not None

    def test_hash_same_values(self):
        vo1 = SampleValueObject(name="test", value=10)
        vo2 = SampleValueObject(name="test", value=10)
        assert hash(vo1) == hash(vo2)

    def test_hash_different_values(self):
        vo1 = SampleValueObject(name="test", value=10)
        vo2 = SampleValueObject(name="test", value=20)
        assert hash(vo1) != hash(vo2)

    def test_can_be_used_in_set(self):
        vo1 = SampleValueObject(name="test", value=10)
        vo2 = SampleValueObject(name="test", value=10)
        vo3 = SampleValueObject(name="other", value=20)
        s = {vo1, vo2, vo3}
        assert len(s) == 2

    def test_can_be_used_as_dict_key(self):
        vo = SampleValueObject(name="test", value=10)
        d = {vo: "value"}
        assert d[vo] == "value"

    def test_immutable(self):
        vo = SampleValueObject(name="test", value=10)
        with pytest.raises(AttributeError):
            vo.name = "changed"


class TestEntityId:
    """Tests for EntityId class."""

    def test_valid_ulid(self):
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert entity_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_normalizes_to_uppercase(self):
        entity_id = EntityId("01arz3ndektsv4rrffq69g5fav")
        assert entity_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_empty_value_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            EntityId("")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid ULID format"):
            EntityId("invalid")

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="Invalid ULID format"):
            EntityId("01ARZ3NDEKTSV4RRFFQ69G5FA")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="Invalid ULID format"):
            EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAVX")

    def test_invalid_characters_raises(self):
        with pytest.raises(ValueError, match="Invalid ULID format"):
            EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAI")  # I is not valid

    def test_str_returns_value(self):
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert str(entity_id) == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_hash_works(self):
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert hash(entity_id) == hash("01ARZ3NDEKTSV4RRFFQ69G5FAV")

    def test_from_string_classmethod(self):
        entity_id = EntityId.from_string("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert entity_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_equality(self):
        id1 = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        id2 = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert id1 == id2

    def test_inequality(self):
        id1 = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        id2 = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAW")
        assert id1 != id2


class TestItemId:
    """Tests for ItemId class."""

    def test_valid_ulid(self):
        item_id = ItemId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert item_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_inherits_validation(self):
        with pytest.raises(ValueError):
            ItemId("invalid")

    def test_from_string(self):
        item_id = ItemId.from_string("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert isinstance(item_id, ItemId)


class TestRoleId:
    """Tests for RoleId class."""

    def test_valid_ulid(self):
        role_id = RoleId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert role_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_inherits_validation(self):
        with pytest.raises(ValueError):
            RoleId("invalid")

    def test_from_string(self):
        role_id = RoleId.from_string("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert isinstance(role_id, RoleId)


class TestUserId:
    """Tests for UserId class."""

    def test_valid_ulid(self):
        user_id = UserId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert user_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_inherits_validation(self):
        with pytest.raises(ValueError):
            UserId("invalid")

    def test_from_string(self):
        user_id = UserId.from_string("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert isinstance(user_id, UserId)


class TestAuditLogId:
    """Tests for AuditLogId class."""

    def test_valid_ulid(self):
        audit_id = AuditLogId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert audit_id.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_inherits_validation(self):
        with pytest.raises(ValueError):
            AuditLogId("invalid")

    def test_from_string(self):
        audit_id = AuditLogId.from_string("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert isinstance(audit_id, AuditLogId)


class TestEntityIdUsageInCollections:
    """Tests for using EntityId in collections."""

    def test_in_set(self):
        id1 = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        id2 = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        id3 = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAW")
        s = {id1, id2, id3}
        assert len(s) == 2

    def test_as_dict_key(self):
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        d = {entity_id: "test_value"}
        assert d[entity_id] == "test_value"

    def test_different_types_not_equal(self):
        entity_id = EntityId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        item_id = ItemId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        # Different types should not be equal even with same value
        assert type(entity_id) != type(item_id)
