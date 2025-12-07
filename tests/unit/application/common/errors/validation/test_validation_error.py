"""Tests for validation error class.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

import pytest

from application.common.errors.base.application_error import ApplicationError
from application.common.errors.validation.validation_error import ValidationError


class TestValidationError:
    """Tests for ValidationError."""

    def test_create_with_message_only(self) -> None:
        """Test creating error with message only."""
        error = ValidationError("Validation failed")
        assert error.message == "Validation failed"
        assert error.errors == []

    def test_create_with_single_error(self) -> None:
        """Test creating error with single field error."""
        errors = [{"field": "email", "message": "Invalid format", "code": "invalid"}]
        error = ValidationError("Validation failed", errors=errors)
        assert len(error.errors) == 1
        assert error.errors[0]["field"] == "email"

    def test_create_with_multiple_errors(self) -> None:
        """Test creating error with multiple field errors."""
        errors = [
            {"field": "email", "message": "Invalid format", "code": "invalid_email"},
            {"field": "age", "message": "Must be >= 18", "code": "min_value"},
            {"field": "name", "message": "Required", "code": "required"},
        ]
        error = ValidationError("Validation failed", errors=errors)
        assert len(error.errors) == 3

    def test_error_code_is_validation_error(self) -> None:
        """Test that error code is VALIDATION_ERROR."""
        error = ValidationError("Test")
        assert error.code == "VALIDATION_ERROR"

    def test_details_contain_errors(self) -> None:
        """Test that details contain errors list."""
        errors = [{"field": "test", "message": "error", "code": "err"}]
        error = ValidationError("Test", errors=errors)
        assert error.details["errors"] == errors

    def test_inherits_from_application_error(self) -> None:
        """Test that ValidationError inherits from ApplicationError."""
        error = ValidationError("Test")
        assert isinstance(error, ApplicationError)

    def test_str_with_no_errors(self) -> None:
        """Test string representation with no errors."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"

    def test_str_with_single_error(self) -> None:
        """Test string representation with single error."""
        errors = [{"field": "email", "message": "Invalid"}]
        error = ValidationError("Validation failed", errors=errors)
        assert "email: Invalid" in str(error)

    def test_str_with_multiple_errors(self) -> None:
        """Test string representation with multiple errors."""
        errors = [
            {"field": "email", "message": "Invalid"},
            {"field": "name", "message": "Required"},
        ]
        error = ValidationError("Validation failed", errors=errors)
        result = str(error)
        assert "email: Invalid" in result
        assert "name: Required" in result

    def test_str_with_missing_field(self) -> None:
        """Test string representation with missing field key."""
        errors = [{"message": "Some error"}]
        error = ValidationError("Validation failed", errors=errors)
        assert "unknown: Some error" in str(error)

    def test_str_with_missing_message(self) -> None:
        """Test string representation with missing message key."""
        errors = [{"field": "test"}]
        error = ValidationError("Validation failed", errors=errors)
        assert "test: invalid" in str(error)

    def test_can_be_raised(self) -> None:
        """Test that error can be raised and caught."""
        errors = [{"field": "test", "message": "error", "code": "err"}]
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test", errors=errors)
        assert len(exc_info.value.errors) == 1

    def test_errors_default_to_empty_list(self) -> None:
        """Test that errors default to empty list."""
        error = ValidationError("Test", errors=None)
        assert error.errors == []

    def test_error_with_extra_fields(self) -> None:
        """Test error with extra fields in error dict."""
        errors = [
            {
                "field": "email",
                "message": "Invalid",
                "code": "invalid",
                "value": "bad@",
                "constraint": "email_format",
            }
        ]
        error = ValidationError("Validation failed", errors=errors)
        assert error.errors[0]["value"] == "bad@"
        assert error.errors[0]["constraint"] == "email_format"
