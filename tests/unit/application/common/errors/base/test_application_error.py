"""Tests for application error classes.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

import pytest

from application.common.errors.base.application_error import ApplicationError
from application.common.errors.base.handler_not_found import HandlerNotFoundError


class TestApplicationError:
    """Tests for ApplicationError."""

    def test_create_with_message_only(self) -> None:
        """Test creating error with message only."""
        error = ApplicationError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.code is None
        assert error.details == {}

    def test_create_with_code(self) -> None:
        """Test creating error with code."""
        error = ApplicationError("Error", code="ERR_001")
        assert error.code == "ERR_001"

    def test_create_with_details(self) -> None:
        """Test creating error with details."""
        details = {"field": "email", "reason": "invalid"}
        error = ApplicationError("Validation error", details=details)
        assert error.details == details

    def test_create_with_all_params(self) -> None:
        """Test creating error with all parameters."""
        error = ApplicationError(
            message="Operation failed",
            code="OP_FAILED",
            details={"operation": "create"},
        )
        assert error.message == "Operation failed"
        assert error.code == "OP_FAILED"
        assert error.details == {"operation": "create"}

    def test_inherits_from_exception(self) -> None:
        """Test that ApplicationError inherits from Exception."""
        error = ApplicationError("test")
        assert isinstance(error, Exception)

    def test_str_representation(self) -> None:
        """Test string representation."""
        error = ApplicationError("Test message")
        assert str(error) == "Test message"

    def test_can_be_raised(self) -> None:
        """Test that error can be raised and caught."""
        with pytest.raises(ApplicationError) as exc_info:
            raise ApplicationError("Test error", code="TEST")
        assert exc_info.value.code == "TEST"

    def test_details_default_to_empty_dict(self) -> None:
        """Test that details default to empty dict."""
        error = ApplicationError("Error", details=None)
        assert error.details == {}

    def test_empty_message(self) -> None:
        """Test error with empty message."""
        error = ApplicationError("")
        assert error.message == ""

    def test_complex_details(self) -> None:
        """Test error with complex details."""
        details = {
            "errors": [
                {"field": "name", "error": "required"},
                {"field": "email", "error": "invalid"},
            ],
            "count": 2,
        }
        error = ApplicationError("Multiple errors", details=details)
        assert len(error.details["errors"]) == 2


class TestHandlerNotFoundError:
    """Tests for HandlerNotFoundError."""

    def test_create_with_handler_type(self) -> None:
        """Test creating error with handler type."""

        class CreateUserCommand:
            pass

        error = HandlerNotFoundError(CreateUserCommand)
        assert error.handler_type == CreateUserCommand
        assert "CreateUserCommand" in error.message

    def test_error_code(self) -> None:
        """Test error code is set correctly."""

        class TestCommand:
            pass

        error = HandlerNotFoundError(TestCommand)
        assert error.code == "HANDLER_NOT_FOUND"

    def test_details_contain_handler_type(self) -> None:
        """Test details contain handler type name."""

        class MyQuery:
            pass

        error = HandlerNotFoundError(MyQuery)
        assert error.details["handler_type"] == "MyQuery"

    def test_inherits_from_application_error(self) -> None:
        """Test that HandlerNotFoundError inherits from ApplicationError."""

        class TestHandler:
            pass

        error = HandlerNotFoundError(TestHandler)
        assert isinstance(error, ApplicationError)

    def test_message_format(self) -> None:
        """Test message format."""

        class GetUserQuery:
            pass

        error = HandlerNotFoundError(GetUserQuery)
        assert error.message == "No handler registered for GetUserQuery"

    def test_can_be_raised(self) -> None:
        """Test that error can be raised and caught."""

        class DeleteCommand:
            pass

        with pytest.raises(HandlerNotFoundError) as exc_info:
            raise HandlerNotFoundError(DeleteCommand)
        assert exc_info.value.handler_type == DeleteCommand
