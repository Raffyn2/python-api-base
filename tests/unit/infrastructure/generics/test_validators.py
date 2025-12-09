"""Tests for generics validators module.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 14.3 - Validation Utilities**
"""

import pytest

from infrastructure.generics.core.errors import ValidationError
from infrastructure.generics.core.validators import (
    ValidationResult,
    validate_format,
    validate_non_empty,
    validate_range,
    validate_required,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_default_valid(self) -> None:
        """Test default validation result is valid."""
        result = ValidationResult()
        assert result.valid is True
        assert result.errors == []

    def test_add_error(self) -> None:
        """Test adding an error."""
        result = ValidationResult()
        result.add_error("Test error")
        assert result.valid is False
        assert "Test error" in result.errors

    def test_add_multiple_errors(self) -> None:
        """Test adding multiple errors."""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_error("Error 2")
        assert result.valid is False
        assert len(result.errors) == 2

    def test_merge_valid_results(self) -> None:
        """Test merging two valid results."""
        result1 = ValidationResult()
        result2 = ValidationResult()
        merged = result1.merge(result2)
        assert merged.valid is True
        assert merged.errors == []

    def test_merge_invalid_result(self) -> None:
        """Test merging with invalid result."""
        result1 = ValidationResult()
        result2 = ValidationResult()
        result2.add_error("Error from result2")
        merged = result1.merge(result2)
        assert merged.valid is False
        assert "Error from result2" in merged.errors

    def test_merge_both_invalid(self) -> None:
        """Test merging two invalid results."""
        result1 = ValidationResult()
        result1.add_error("Error 1")
        result2 = ValidationResult()
        result2.add_error("Error 2")
        merged = result1.merge(result2)
        assert merged.valid is False
        assert len(merged.errors) == 2


class TestValidateNonEmpty:
    """Tests for validate_non_empty function."""

    def test_valid_string(self) -> None:
        """Test with valid non-empty string."""
        result = validate_non_empty("hello", "field", raise_error=False)
        assert result.valid is True

    def test_empty_string(self) -> None:
        """Test with empty string."""
        result = validate_non_empty("", "field", raise_error=False)
        assert result.valid is False

    def test_whitespace_string(self) -> None:
        """Test with whitespace-only string."""
        result = validate_non_empty("   ", "field", raise_error=False)
        assert result.valid is False

    def test_none_value(self) -> None:
        """Test with None value."""
        result = validate_non_empty(None, "field", raise_error=False)
        assert result.valid is False

    def test_raises_error(self) -> None:
        """Test that it raises ValidationError when raise_error=True."""
        with pytest.raises(ValidationError):
            validate_non_empty("", "field", raise_error=True)

    def test_no_raise_on_valid(self) -> None:
        """Test no exception on valid input."""
        result = validate_non_empty("valid", "field", raise_error=True)
        assert result.valid is True


class TestValidateRange:
    """Tests for validate_range function."""

    def test_value_in_range(self) -> None:
        """Test value within range."""
        result = validate_range(5, "field", min_value=0, max_value=10, raise_error=False)
        assert result.valid is True

    def test_value_at_min(self) -> None:
        """Test value at minimum."""
        result = validate_range(0, "field", min_value=0, max_value=10, raise_error=False)
        assert result.valid is True

    def test_value_at_max(self) -> None:
        """Test value at maximum."""
        result = validate_range(10, "field", min_value=0, max_value=10, raise_error=False)
        assert result.valid is True

    def test_value_below_min(self) -> None:
        """Test value below minimum."""
        result = validate_range(-1, "field", min_value=0, max_value=10, raise_error=False)
        assert result.valid is False

    def test_value_above_max(self) -> None:
        """Test value above maximum."""
        result = validate_range(11, "field", min_value=0, max_value=10, raise_error=False)
        assert result.valid is False

    def test_only_min_value(self) -> None:
        """Test with only min_value specified."""
        result = validate_range(5, "field", min_value=0, raise_error=False)
        assert result.valid is True

    def test_only_max_value(self) -> None:
        """Test with only max_value specified."""
        result = validate_range(5, "field", max_value=10, raise_error=False)
        assert result.valid is True

    def test_float_values(self) -> None:
        """Test with float values."""
        result = validate_range(5.5, "field", min_value=0.0, max_value=10.0, raise_error=False)
        assert result.valid is True

    def test_raises_error_below_min(self) -> None:
        """Test raises error when below min."""
        with pytest.raises(ValidationError):
            validate_range(-1, "field", min_value=0, raise_error=True)

    def test_raises_error_above_max(self) -> None:
        """Test raises error when above max."""
        with pytest.raises(ValidationError):
            validate_range(11, "field", max_value=10, raise_error=True)


class TestValidateFormat:
    """Tests for validate_format function."""

    def test_matching_pattern(self) -> None:
        """Test string matching pattern."""
        result = validate_format("abc123", "field", r"^[a-z]+\d+$", raise_error=False)
        assert result.valid is True

    def test_non_matching_pattern(self) -> None:
        """Test string not matching pattern."""
        result = validate_format("123abc", "field", r"^[a-z]+\d+$", raise_error=False)
        assert result.valid is False

    def test_email_pattern(self) -> None:
        """Test email-like pattern."""
        result = validate_format(
            "test@example.com",
            "email",
            r"^[\w\.-]+@[\w\.-]+\.\w+$",
            raise_error=False,
        )
        assert result.valid is True

    def test_raises_error(self) -> None:
        """Test raises error on mismatch."""
        with pytest.raises(ValidationError):
            validate_format("invalid", "field", r"^\d+$", raise_error=True)


class TestValidateRequired:
    """Tests for validate_required function."""

    def test_non_none_value(self) -> None:
        """Test with non-None value."""
        result = validate_required("value", "field", raise_error=False)
        assert result.valid is True

    def test_none_value(self) -> None:
        """Test with None value."""
        result = validate_required(None, "field", raise_error=False)
        assert result.valid is False

    def test_empty_string_is_valid(self) -> None:
        """Test that empty string is considered valid (not None)."""
        result = validate_required("", "field", raise_error=False)
        assert result.valid is True

    def test_zero_is_valid(self) -> None:
        """Test that zero is considered valid."""
        result = validate_required(0, "field", raise_error=False)
        assert result.valid is True

    def test_false_is_valid(self) -> None:
        """Test that False is considered valid."""
        result = validate_required(False, "field", raise_error=False)
        assert result.valid is True

    def test_raises_error(self) -> None:
        """Test raises error on None."""
        with pytest.raises(ValidationError):
            validate_required(None, "field", raise_error=True)
