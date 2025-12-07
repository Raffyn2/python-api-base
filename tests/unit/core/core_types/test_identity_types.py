"""Unit tests for identity type definitions.

Tests ULID, UUID, UUID7, and EntityId type aliases.
"""

import pytest
from pydantic import BaseModel, ValidationError

from core.types.identity.id_types import ULID, UUID, UUID7, EntityId


class ULIDModel(BaseModel):
    """Model with ULID field."""
    id: ULID


class UUIDModel(BaseModel):
    """Model with UUID field."""
    id: UUID


class UUID7Model(BaseModel):
    """Model with UUID7 field."""
    id: UUID7


class TestULID:
    """Tests for ULID type."""

    def test_valid_ulid(self) -> None:
        """Test valid ULID is accepted."""
        model = ULIDModel(id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert model.id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_valid_ulid_lowercase(self) -> None:
        """Test ULID pattern is case-sensitive (uppercase only)."""
        # ULID uses Crockford Base32 which is uppercase
        with pytest.raises(ValidationError):
            ULIDModel(id="01arz3ndektsv4rrffq69g5fav")

    def test_invalid_ulid_too_short(self) -> None:
        """Test ULID too short is rejected."""
        with pytest.raises(ValidationError):
            ULIDModel(id="01ARZ3NDEKTSV4RRFFQ69G5FA")

    def test_invalid_ulid_too_long(self) -> None:
        """Test ULID too long is rejected."""
        with pytest.raises(ValidationError):
            ULIDModel(id="01ARZ3NDEKTSV4RRFFQ69G5FAVX")

    def test_invalid_ulid_bad_chars(self) -> None:
        """Test ULID with invalid characters is rejected."""
        # I, L, O, U are not valid in Crockford Base32
        with pytest.raises(ValidationError):
            ULIDModel(id="01ARZ3NDEKTSV4RRFFQ69G5FAI")


class TestUUID:
    """Tests for UUID type."""

    def test_valid_uuid(self) -> None:
        """Test valid UUID is accepted."""
        model = UUIDModel(id="550e8400-e29b-41d4-a716-446655440000")
        assert model.id == "550e8400-e29b-41d4-a716-446655440000"

    def test_valid_uuid_lowercase(self) -> None:
        """Test UUID accepts lowercase."""
        model = UUIDModel(id="550e8400-e29b-41d4-a716-446655440000")
        assert model.id == "550e8400-e29b-41d4-a716-446655440000"

    def test_invalid_uuid_no_hyphens(self) -> None:
        """Test UUID without hyphens is rejected."""
        with pytest.raises(ValidationError):
            UUIDModel(id="550e8400e29b41d4a716446655440000")

    def test_invalid_uuid_too_short(self) -> None:
        """Test UUID too short is rejected."""
        with pytest.raises(ValidationError):
            UUIDModel(id="550e8400-e29b-41d4-a716-44665544000")

    def test_invalid_uuid_uppercase(self) -> None:
        """Test UUID with uppercase is rejected (pattern requires lowercase)."""
        with pytest.raises(ValidationError):
            UUIDModel(id="550E8400-E29B-41D4-A716-446655440000")


class TestUUID7:
    """Tests for UUID7 type."""

    def test_valid_uuid7(self) -> None:
        """Test valid UUID7 is accepted."""
        # UUID7 has version 7 in position 13 and variant 8-b in position 17
        model = UUID7Model(id="01902e8c-7000-7000-8000-000000000000")
        assert model.id == "01902e8c-7000-7000-8000-000000000000"

    def test_invalid_uuid7_wrong_version(self) -> None:
        """Test UUID with wrong version is rejected."""
        # Version 4 UUID (has 4 in position 13)
        with pytest.raises(ValidationError):
            UUID7Model(id="550e8400-e29b-41d4-a716-446655440000")

    def test_invalid_uuid7_wrong_variant(self) -> None:
        """Test UUID7 with wrong variant is rejected."""
        # Wrong variant (not 8, 9, a, or b in position 17)
        with pytest.raises(ValidationError):
            UUID7Model(id="01902e8c-7000-7000-0000-000000000000")


class TestEntityId:
    """Tests for EntityId type alias."""

    def test_string_entity_id(self) -> None:
        """Test string is valid EntityId."""
        entity_id: EntityId = "entity-123"
        assert entity_id == "entity-123"

    def test_int_entity_id(self) -> None:
        """Test int is valid EntityId."""
        entity_id: EntityId = 123
        assert entity_id == 123

    def test_entity_id_in_function(self) -> None:
        """Test EntityId can be used in function signatures."""
        def get_entity(id: EntityId) -> str:
            return f"Entity: {id}"
        
        assert get_entity("abc") == "Entity: abc"
        assert get_entity(123) == "Entity: 123"
