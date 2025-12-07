"""Tests for numeric type definitions.

Tests PositiveInt, NonNegativeInt, Percentage, PageNumber, etc.
"""

import pytest
from pydantic import BaseModel, ValidationError

from core.types import (
    NonNegativeFloat,
    NonNegativeInt,
    PageNumber,
    PageSize,
    Percentage,
    PositiveFloat,
    PositiveInt,
)


class PositiveIntModel(BaseModel):
    """Model for testing PositiveInt."""

    value: PositiveInt


class NonNegativeIntModel(BaseModel):
    """Model for testing NonNegativeInt."""

    value: NonNegativeInt


class PositiveFloatModel(BaseModel):
    """Model for testing PositiveFloat."""

    value: PositiveFloat


class NonNegativeFloatModel(BaseModel):
    """Model for testing NonNegativeFloat."""

    value: NonNegativeFloat


class PercentageModel(BaseModel):
    """Model for testing Percentage."""

    value: Percentage


class PageNumberModel(BaseModel):
    """Model for testing PageNumber."""

    value: PageNumber


class PageSizeModel(BaseModel):
    """Model for testing PageSize."""

    value: PageSize


class TestPositiveInt:
    """Tests for PositiveInt type."""

    def test_valid_positive_int(self) -> None:
        model = PositiveIntModel(value=1)
        assert model.value == 1

    def test_large_positive_int(self) -> None:
        model = PositiveIntModel(value=1000000)
        assert model.value == 1000000

    def test_zero_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PositiveIntModel(value=0)

    def test_negative_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PositiveIntModel(value=-1)


class TestNonNegativeInt:
    """Tests for NonNegativeInt type."""

    def test_valid_positive(self) -> None:
        model = NonNegativeIntModel(value=1)
        assert model.value == 1

    def test_zero_valid(self) -> None:
        model = NonNegativeIntModel(value=0)
        assert model.value == 0

    def test_negative_invalid(self) -> None:
        with pytest.raises(ValidationError):
            NonNegativeIntModel(value=-1)


class TestPositiveFloat:
    """Tests for PositiveFloat type."""

    def test_valid_positive(self) -> None:
        model = PositiveFloatModel(value=0.1)
        assert model.value == 0.1

    def test_large_positive(self) -> None:
        model = PositiveFloatModel(value=1000.5)
        assert model.value == 1000.5

    def test_zero_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PositiveFloatModel(value=0.0)

    def test_negative_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PositiveFloatModel(value=-0.1)


class TestNonNegativeFloat:
    """Tests for NonNegativeFloat type."""

    def test_valid_positive(self) -> None:
        model = NonNegativeFloatModel(value=0.1)
        assert model.value == 0.1

    def test_zero_valid(self) -> None:
        model = NonNegativeFloatModel(value=0.0)
        assert model.value == 0.0

    def test_negative_invalid(self) -> None:
        with pytest.raises(ValidationError):
            NonNegativeFloatModel(value=-0.1)


class TestPercentage:
    """Tests for Percentage type."""

    def test_valid_zero(self) -> None:
        model = PercentageModel(value=0.0)
        assert model.value == 0.0

    def test_valid_hundred(self) -> None:
        model = PercentageModel(value=100.0)
        assert model.value == 100.0

    def test_valid_middle(self) -> None:
        model = PercentageModel(value=50.5)
        assert model.value == 50.5

    def test_negative_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PercentageModel(value=-1.0)

    def test_over_hundred_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PercentageModel(value=100.1)


class TestPageNumber:
    """Tests for PageNumber type."""

    def test_valid_first_page(self) -> None:
        model = PageNumberModel(value=1)
        assert model.value == 1

    def test_valid_large_page(self) -> None:
        model = PageNumberModel(value=10000)
        assert model.value == 10000

    def test_zero_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PageNumberModel(value=0)

    def test_negative_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PageNumberModel(value=-1)

    def test_over_max_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PageNumberModel(value=10001)


class TestPageSize:
    """Tests for PageSize type."""

    def test_valid_min(self) -> None:
        model = PageSizeModel(value=1)
        assert model.value == 1

    def test_valid_max(self) -> None:
        model = PageSizeModel(value=100)
        assert model.value == 100

    def test_valid_middle(self) -> None:
        model = PageSizeModel(value=50)
        assert model.value == 50

    def test_zero_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PageSizeModel(value=0)

    def test_over_max_invalid(self) -> None:
        with pytest.raises(ValidationError):
            PageSizeModel(value=101)
