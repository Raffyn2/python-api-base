"""Tests for numeric types module.

Tests Pydantic annotated types for numeric validation.
"""

import pytest
from pydantic import BaseModel, ValidationError

# Import using full path to avoid conflict with Python's built-in types module
from core.types.data.numeric_types import (
    NonNegativeFloat,
    NonNegativeInt,
    PageNumber,
    PageSize,
    Percentage,
    PercentageRange,
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


class PercentageRangeModel(BaseModel):
    """Model for testing PercentageRange."""

    value: PercentageRange


class PageNumberModel(BaseModel):
    """Model for testing PageNumber."""

    value: PageNumber


class PageSizeModel(BaseModel):
    """Model for testing PageSize."""

    value: PageSize


class TestPositiveInt:
    """Tests for PositiveInt type."""

    def test_valid_positive(self) -> None:
        model = PositiveIntModel(value=1)
        assert model.value == 1

    def test_valid_large_positive(self) -> None:
        model = PositiveIntModel(value=1000000)
        assert model.value == 1000000

    def test_invalid_zero(self) -> None:
        with pytest.raises(ValidationError):
            PositiveIntModel(value=0)

    def test_invalid_negative(self) -> None:
        with pytest.raises(ValidationError):
            PositiveIntModel(value=-1)


class TestNonNegativeInt:
    """Tests for NonNegativeInt type."""

    def test_valid_zero(self) -> None:
        model = NonNegativeIntModel(value=0)
        assert model.value == 0

    def test_valid_positive(self) -> None:
        model = NonNegativeIntModel(value=100)
        assert model.value == 100

    def test_invalid_negative(self) -> None:
        with pytest.raises(ValidationError):
            NonNegativeIntModel(value=-1)


class TestPositiveFloat:
    """Tests for PositiveFloat type."""

    def test_valid_positive(self) -> None:
        model = PositiveFloatModel(value=0.1)
        assert model.value == 0.1

    def test_valid_large_positive(self) -> None:
        model = PositiveFloatModel(value=999.99)
        assert model.value == 999.99

    def test_invalid_zero(self) -> None:
        with pytest.raises(ValidationError):
            PositiveFloatModel(value=0.0)

    def test_invalid_negative(self) -> None:
        with pytest.raises(ValidationError):
            PositiveFloatModel(value=-0.1)


class TestNonNegativeFloat:
    """Tests for NonNegativeFloat type."""

    def test_valid_zero(self) -> None:
        model = NonNegativeFloatModel(value=0.0)
        assert model.value == 0.0

    def test_valid_positive(self) -> None:
        model = NonNegativeFloatModel(value=50.5)
        assert model.value == 50.5

    def test_invalid_negative(self) -> None:
        with pytest.raises(ValidationError):
            NonNegativeFloatModel(value=-0.01)


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

    def test_invalid_negative(self) -> None:
        with pytest.raises(ValidationError):
            PercentageModel(value=-1.0)

    def test_invalid_over_hundred(self) -> None:
        with pytest.raises(ValidationError):
            PercentageModel(value=100.1)


class TestPercentageRange:
    """Tests for PercentageRange type."""

    def test_valid_range(self) -> None:
        model = PercentageRangeModel(value=(0.0, 100.0))
        assert model.value == (0.0, 100.0)

    def test_valid_narrow_range(self) -> None:
        model = PercentageRangeModel(value=(25.0, 75.0))
        assert model.value == (25.0, 75.0)

    def test_valid_same_values(self) -> None:
        model = PercentageRangeModel(value=(50.0, 50.0))
        assert model.value == (50.0, 50.0)


class TestPageNumber:
    """Tests for PageNumber type."""

    def test_valid_first_page(self) -> None:
        model = PageNumberModel(value=1)
        assert model.value == 1

    def test_valid_max_page(self) -> None:
        model = PageNumberModel(value=10000)
        assert model.value == 10000

    def test_valid_middle_page(self) -> None:
        model = PageNumberModel(value=500)
        assert model.value == 500

    def test_invalid_zero(self) -> None:
        with pytest.raises(ValidationError):
            PageNumberModel(value=0)

    def test_invalid_negative(self) -> None:
        with pytest.raises(ValidationError):
            PageNumberModel(value=-1)

    def test_invalid_over_max(self) -> None:
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

    def test_valid_common_size(self) -> None:
        model = PageSizeModel(value=20)
        assert model.value == 20

    def test_invalid_zero(self) -> None:
        with pytest.raises(ValidationError):
            PageSizeModel(value=0)

    def test_invalid_over_max(self) -> None:
        with pytest.raises(ValidationError):
            PageSizeModel(value=101)

    def test_invalid_negative(self) -> None:
        with pytest.raises(ValidationError):
            PageSizeModel(value=-10)
