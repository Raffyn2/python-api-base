"""Property-based tests for type validation.

**Feature: test-coverage-80-percent, Property 2: Validator Consistency**
**Validates: Requirements 7.2**
"""

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import BaseModel, ValidationError

from core.types import (
    ULID,
    UUID,
    NonNegativeInt,
    PageNumber,
    PageSize,
    Percentage,
    PositiveInt,
    Slug,
)


class ULIDModel(BaseModel):
    id: ULID


class UUIDModel(BaseModel):
    id: UUID


class PositiveIntModel(BaseModel):
    value: PositiveInt


class NonNegativeIntModel(BaseModel):
    value: NonNegativeInt


class PercentageModel(BaseModel):
    value: Percentage


class PageNumberModel(BaseModel):
    value: PageNumber


class PageSizeModel(BaseModel):
    value: PageSize


class SlugModel(BaseModel):
    value: Slug


ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


class TestTypeValidationProperties:
    """Property-based tests for type validation consistency."""

    @given(ulid=st.text(alphabet=ULID_ALPHABET, min_size=26, max_size=26))
    @settings(max_examples=50)
    def test_ulid_valid_format_accepted(self, ulid: str) -> None:
        """
        **Feature: test-coverage-80-percent, Property 2: Validator Consistency**

        For any string of 26 Crockford Base32 characters,
        ULID validation SHALL accept the value.
        """
        model = ULIDModel(id=ulid)
        assert model.id == ulid

    @given(
        uuid=st.from_regex(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            fullmatch=True,
        )
    )
    @settings(max_examples=50)
    def test_uuid_valid_format_accepted(self, uuid: str) -> None:
        """
        **Feature: test-coverage-80-percent, Property 2: Validator Consistency**

        For any string matching UUID format,
        UUID validation SHALL accept the value.
        """
        model = UUIDModel(id=uuid)
        assert model.id == uuid

    @given(value=st.integers(min_value=1, max_value=100000))
    @settings(max_examples=50)
    def test_positive_int_valid_values_accepted(self, value: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 2: Validator Consistency**

        For any integer > 0, PositiveInt validation SHALL accept the value.
        """
        model = PositiveIntModel(value=value)
        assert model.value == value

    @given(value=st.integers(max_value=0))
    @settings(max_examples=30)
    def test_positive_int_invalid_values_rejected(self, value: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 2: Validator Consistency**

        For any integer <= 0, PositiveInt validation SHALL reject the value.
        """
        with pytest.raises(ValidationError):
            PositiveIntModel(value=value)

    @given(value=st.floats(min_value=0.0, max_value=100.0, allow_nan=False))
    @settings(max_examples=50)
    def test_percentage_valid_values_accepted(self, value: float) -> None:
        """
        **Feature: test-coverage-80-percent, Property 2: Validator Consistency**

        For any float between 0 and 100, Percentage validation SHALL accept.
        """
        model = PercentageModel(value=value)
        assert model.value == value

    @given(value=st.integers(min_value=1, max_value=10000))
    @settings(max_examples=50)
    def test_page_number_valid_values_accepted(self, value: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 2: Validator Consistency**

        For any integer between 1 and 10000, PageNumber SHALL accept.
        """
        model = PageNumberModel(value=value)
        assert model.value == value

    @given(value=st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_page_size_valid_values_accepted(self, value: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 2: Validator Consistency**

        For any integer between 1 and 100, PageSize SHALL accept.
        """
        model = PageSizeModel(value=value)
        assert model.value == value
