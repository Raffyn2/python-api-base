"""Tests for ID type definitions.

Tests ULID, UUID, UUID7 types.
"""

import pytest
from pydantic import BaseModel, ValidationError

from core.types import ULID, UUID, UUID7


class ULIDModel(BaseModel):
    """Model for testing ULID."""

    value: ULID


class UUIDModel(BaseModel):
    """Model for testing UUID."""

    value: UUID


class UUID7Model(BaseModel):
    """Model for testing UUID7."""

    value: UUID7


class TestULID:
    """Tests for ULID type."""

    def test_valid_ulid(self) -> None:
        model = ULIDModel(value="01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert model.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_valid_ulid_lowercase_invalid(self) -> None:
        # ULID uses Crockford Base32 which is uppercase
        with pytest.raises(ValidationError):
            ULIDModel(value="01arz3ndektsv4rrffq69g5fav")

    def test_too_short_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ULIDModel(value="01ARZ3NDEKTSV4RRFFQ69G5FA")  # 25 chars

    def test_too_long_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ULIDModel(value="01ARZ3NDEKTSV4RRFFQ69G5FAVX")  # 27 chars

    def test_invalid_characters(self) -> None:
        # ULID doesn't use I, L, O, U
        with pytest.raises(ValidationError):
            ULIDModel(value="01ARZ3NDEKTSV4RRFFQ69G5FAI")

    def test_empty_invalid(self) -> None:
        with pytest.raises(ValidationError):
            ULIDModel(value="")


class TestUUID:
    """Tests for UUID type."""

    def test_valid_uuid(self) -> None:
        model = UUIDModel(value="550e8400-e29b-41d4-a716-446655440000")
        assert model.value == "550e8400-e29b-41d4-a716-446655440000"

    def test_valid_uuid_v4(self) -> None:
        model = UUIDModel(value="f47ac10b-58cc-4372-a567-0e02b2c3d479")
        assert model.value == "f47ac10b-58cc-4372-a567-0e02b2c3d479"

    def test_uppercase_valid(self) -> None:
        # UUID pattern is case-insensitive (accepts a-fA-F)
        model = UUIDModel(value="550E8400-E29B-41D4-A716-446655440000")
        assert model.value == "550E8400-E29B-41D4-A716-446655440000"

    def test_no_hyphens_invalid(self) -> None:
        with pytest.raises(ValidationError):
            UUIDModel(value="550e8400e29b41d4a716446655440000")

    def test_too_short_invalid(self) -> None:
        with pytest.raises(ValidationError):
            UUIDModel(value="550e8400-e29b-41d4-a716-44665544000")

    def test_too_long_invalid(self) -> None:
        with pytest.raises(ValidationError):
            UUIDModel(value="550e8400-e29b-41d4-a716-4466554400000")

    def test_invalid_characters(self) -> None:
        with pytest.raises(ValidationError):
            UUIDModel(value="550e8400-e29b-41d4-a716-44665544000g")

    def test_empty_invalid(self) -> None:
        with pytest.raises(ValidationError):
            UUIDModel(value="")


class TestUUID7:
    """Tests for UUID7 type."""

    def test_valid_uuid7(self) -> None:
        # UUID7 has version 7 in position 13 and variant 8/9/a/b in position 17
        model = UUID7Model(value="01902f4a-7b8c-7def-8123-456789abcdef")
        assert model.value == "01902f4a-7b8c-7def-8123-456789abcdef"

    def test_valid_uuid7_variant_9(self) -> None:
        model = UUID7Model(value="01902f4a-7b8c-7def-9123-456789abcdef")
        assert model.value == "01902f4a-7b8c-7def-9123-456789abcdef"

    def test_valid_uuid7_variant_a(self) -> None:
        model = UUID7Model(value="01902f4a-7b8c-7def-a123-456789abcdef")
        assert model.value == "01902f4a-7b8c-7def-a123-456789abcdef"

    def test_valid_uuid7_variant_b(self) -> None:
        model = UUID7Model(value="01902f4a-7b8c-7def-b123-456789abcdef")
        assert model.value == "01902f4a-7b8c-7def-b123-456789abcdef"

    def test_wrong_version_invalid(self) -> None:
        # Version 4 instead of 7
        with pytest.raises(ValidationError):
            UUID7Model(value="01902f4a-7b8c-4def-8123-456789abcdef")

    def test_wrong_variant_invalid(self) -> None:
        # Variant 0 instead of 8/9/a/b
        with pytest.raises(ValidationError):
            UUID7Model(value="01902f4a-7b8c-7def-0123-456789abcdef")

    def test_uppercase_valid(self) -> None:
        # UUID7 pattern is case-insensitive (accepts a-fA-F)
        model = UUID7Model(value="01902F4A-7B8C-7DEF-8123-456789ABCDEF")
        assert model.value == "01902F4A-7B8C-7DEF-8123-456789ABCDEF"

    def test_empty_invalid(self) -> None:
        with pytest.raises(ValidationError):
            UUID7Model(value="")
