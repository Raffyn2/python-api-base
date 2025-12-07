"""Unit tests for application error classes.

Tests ApplicationError, HandlerNotFoundError, ValidationError, and related errors.
"""

import pytest

from application.common.errors import (
    ApplicationError,
    ConflictError,
    ForbiddenError,
    HandlerNotFoundError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestApplicationError:
    """Tests for ApplicationError base class."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = ApplicationError(message="Something went wrong")
        assert error.message == "Something went wrong"
        assert error.code is None
        assert error.details == {}
        assert str(error) == "Something went wrong"

    def test_error_with_code(self) -> None:
        """Test error with code."""
        error = ApplicationError(
            message="Operation failed",
            code="OPERATION_FAILED",
        )
        assert error.code == "OPERATION_FAILED"

    def test_error_with_details(self) -> None:
        """Test error with details."""
        error = ApplicationError(
            message="Failed",
            code="FAILED",
            details={"operation": "create", "entity": "user"},
        )
        assert error.details["operation"] == "create"
        assert error.details["entity"] == "user"

    def test_error_is_exception(self) -> None:
        """Test error is an Exception."""
        error = ApplicationError(message="Error")
        assert isinstance(error, Exception)

    def test_error_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(ApplicationError) as exc_info:
            raise ApplicationError(message="Test error", code="TEST")
        assert exc_info.value.message == "Test error"
        assert exc_info.value.code == "TEST"


class TestHandlerNotFoundError:
    """Tests for HandlerNotFoundError."""

    def test_handler_not_found(self) -> None:
        """Test handler not found error."""

        class TestCommand:
            pass

        error = HandlerNotFoundError(TestCommand)
        assert error.handler_type == TestCommand
        assert "TestCommand" in error.message
        assert error.code == "HANDLER_NOT_FOUND"
        assert error.details["handler_type"] == "TestCommand"

    def test_inherits_application_error(self) -> None:
        """Test inherits from ApplicationError."""

        class TestQuery:
            pass

        error = HandlerNotFoundError(TestQuery)
        assert isinstance(error, ApplicationError)


class TestValidationError:
    """Tests for ValidationError."""

    def test_basic_validation_error(self) -> None:
        """Test basic validation error."""
        error = ValidationError(message="Validation failed")
        assert error.message == "Validation failed"
        assert error.code == "VALIDATION_ERROR"
        assert error.errors == []

    def test_validation_error_with_field_errors(self) -> None:
        """Test validation error with field errors."""
        field_errors = [
            {"field": "email", "message": "Invalid format", "code": "invalid_email"},
            {"field": "age", "message": "Must be >= 18", "code": "min_value"},
        ]
        error = ValidationError(message="Validation failed", errors=field_errors)
        assert len(error.errors) == 2
        assert error.errors[0]["field"] == "email"
        assert error.errors[1]["field"] == "age"

    def test_validation_error_str_with_errors(self) -> None:
        """Test string representation with field errors."""
        field_errors = [
            {"field": "email", "message": "Invalid format"},
        ]
        error = ValidationError(message="Validation failed", errors=field_errors)
        error_str = str(error)
        assert "email" in error_str
        assert "Invalid format" in error_str

    def test_validation_error_str_without_errors(self) -> None:
        """Test string representation without field errors."""
        error = ValidationError(message="Validation failed")
        assert str(error) == "Validation failed"

    def test_validation_error_details(self) -> None:
        """Test validation error details contain errors."""
        field_errors = [{"field": "name", "message": "Required"}]
        error = ValidationError(message="Failed", errors=field_errors)
        assert "errors" in error.details
        assert error.details["errors"] == field_errors


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_not_found_error(self) -> None:
        """Test not found error creation."""
        error = NotFoundError(entity_type="User", entity_id="user-123")
        assert error.entity_type == "User"
        assert error.entity_id == "user-123"
        assert error.code == "NOT_FOUND"
        assert "User" in error.message
        assert "user-123" in error.message

    def test_not_found_error_details(self) -> None:
        """Test not found error details."""
        error = NotFoundError(entity_type="Order", entity_id=456)
        assert error.details["entity_type"] == "Order"
        assert error.details["entity_id"] == "456"

    def test_inherits_application_error(self) -> None:
        """Test inherits from ApplicationError."""
        error = NotFoundError(entity_type="Product", entity_id="prod-1")
        assert isinstance(error, ApplicationError)


class TestConflictError:
    """Tests for ConflictError."""

    def test_conflict_error_basic(self) -> None:
        """Test basic conflict error."""
        error = ConflictError(message="Duplicate entry")
        assert error.message == "Duplicate entry"
        assert error.code == "CONFLICT"
        assert error.details == {}

    def test_conflict_error_with_resource(self) -> None:
        """Test conflict error with resource."""
        error = ConflictError(
            message="User with email already exists",
            resource="User",
        )
        assert error.details["resource"] == "User"

    def test_inherits_application_error(self) -> None:
        """Test inherits from ApplicationError."""
        error = ConflictError(message="Conflict")
        assert isinstance(error, ApplicationError)


class TestForbiddenError:
    """Tests for ForbiddenError."""

    def test_forbidden_error_default(self) -> None:
        """Test forbidden error with default message."""
        error = ForbiddenError()
        assert error.message == "Access denied"
        assert error.code == "FORBIDDEN"

    def test_forbidden_error_custom_message(self) -> None:
        """Test forbidden error with custom message."""
        error = ForbiddenError("You cannot access this resource")
        assert error.message == "You cannot access this resource"

    def test_inherits_application_error(self) -> None:
        """Test inherits from ApplicationError."""
        error = ForbiddenError()
        assert isinstance(error, ApplicationError)


class TestUnauthorizedError:
    """Tests for UnauthorizedError."""

    def test_unauthorized_error_default(self) -> None:
        """Test unauthorized error with default message."""
        error = UnauthorizedError()
        assert error.message == "Authentication required"
        assert error.code == "UNAUTHORIZED"

    def test_unauthorized_error_custom_message(self) -> None:
        """Test unauthorized error with custom message."""
        error = UnauthorizedError("Invalid token")
        assert error.message == "Invalid token"

    def test_inherits_application_error(self) -> None:
        """Test inherits from ApplicationError."""
        error = UnauthorizedError()
        assert isinstance(error, ApplicationError)
