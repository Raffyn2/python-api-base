"""Tests for validation-related exceptions.

**Feature: realistic-test-coverage**
**Validates: Requirements 4.2**
"""

from core.errors.shared.validation_errors import ValidationError


class TestValidationError:
    """Tests for ValidationError."""

    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        error = ValidationError("email", "invalid@", "must be valid email format")
        assert error.field == "email"
        assert error.value == "invalid@"
        assert error.constraint == "must be valid email format"

    def test_message_format(self) -> None:
        """Test error message format."""
        error = ValidationError("age", -5, "must be positive")
        message = str(error)
        assert "Validation failed for 'age'" in message
        assert "must be positive" in message

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""
        error = ValidationError("field", "value", "constraint")
        assert isinstance(error, Exception)

    def test_with_none_value(self) -> None:
        """Test with None as value."""
        error = ValidationError("required_field", None, "cannot be null")
        assert error.value is None
        assert "cannot be null" in str(error)

    def test_with_complex_value(self) -> None:
        """Test with complex object as value."""
        complex_value = {"nested": {"data": [1, 2, 3]}}
        error = ValidationError("config", complex_value, "invalid structure")
        assert error.value == complex_value
        assert "invalid structure" in str(error)

    def test_with_empty_string_value(self) -> None:
        """Test with empty string as value."""
        error = ValidationError("name", "", "cannot be empty")
        assert error.value == ""
        assert "cannot be empty" in str(error)

    def test_with_numeric_value(self) -> None:
        """Test with numeric value."""
        error = ValidationError("quantity", 1000, "must be less than 100")
        assert error.value == 1000
        assert "must be less than 100" in str(error)

    def test_with_boolean_value(self) -> None:
        """Test with boolean value."""
        error = ValidationError("active", False, "must be true")
        assert error.value is False
        assert "must be true" in str(error)

    def test_with_list_value(self) -> None:
        """Test with list value."""
        error = ValidationError("items", [], "cannot be empty list")
        assert error.value == []
        assert "cannot be empty list" in str(error)

    def test_field_name_preserved(self) -> None:
        """Test that field name is preserved exactly."""
        error = ValidationError("user.profile.email", "test", "invalid")
        assert error.field == "user.profile.email"
        assert "user.profile.email" in str(error)
