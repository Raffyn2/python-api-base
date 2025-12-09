"""Unit tests for core/errors/base/domain_errors.py.

Tests domain error creation, message formatting, and serialization.

**Task 4.1: Create tests for domain_errors.py**
**Requirements: 3.3**
"""

from datetime import UTC, datetime

import pytest

from core.errors.base.domain_errors import (
    AppError,
    AppException,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    EntityNotFoundError,
    ErrorContext,
    RateLimitExceededError,
    ValidationError,
)


class TestErrorContext:
    """Tests for ErrorContext dataclass."""

    def test_default_values(self) -> None:
        """Test ErrorContext has default values."""
        ctx = ErrorContext()

        assert ctx.correlation_id is not None
        assert len(ctx.correlation_id) > 0
        assert ctx.timestamp is not None
        assert ctx.request_path is None

    def test_custom_values(self) -> None:
        """Test ErrorContext with custom values."""
        ctx = ErrorContext(
            correlation_id="test-123", request_path="/api/users"
        )

        assert ctx.correlation_id == "test-123"
        assert ctx.request_path == "/api/users"

    def test_immutability(self) -> None:
        """Test ErrorContext is immutable."""
        ctx = ErrorContext()

        with pytest.raises(AttributeError):
            ctx.correlation_id = "new-id"

    def test_to_dict(self) -> None:
        """Test ErrorContext serialization."""
        ctx = ErrorContext(correlation_id="test-123", request_path="/api/test")
        result = ctx.to_dict()

        assert result["correlation_id"] == "test-123"
        assert result["request_path"] == "/api/test"
        assert "timestamp" in result


class TestAppError:
    """Tests for AppError base class."""

    def test_basic_creation(self) -> None:
        """Test basic AppError creation."""
        error = AppError(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
        )

        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.status_code == 400
        assert str(error) == "Test error"

    def test_with_details(self) -> None:
        """Test AppError with details."""
        error = AppError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"field": "value"},
        )

        assert error.details == {"field": "value"}

    def test_with_context(self) -> None:
        """Test AppError with custom context."""
        ctx = ErrorContext(correlation_id="custom-123")
        error = AppError(
            message="Test error", error_code="TEST_ERROR", context=ctx
        )

        assert error.correlation_id == "custom-123"

    def test_correlation_id_property(self) -> None:
        """Test correlation_id property."""
        error = AppError(message="Test", error_code="TEST")
        assert error.correlation_id is not None

    def test_timestamp_property(self) -> None:
        """Test timestamp property."""
        error = AppError(message="Test", error_code="TEST")
        assert isinstance(error.timestamp, datetime)

    def test_to_dict(self) -> None:
        """Test AppError serialization."""
        error = AppError(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"key": "value"},
        )
        result = error.to_dict()

        assert result["message"] == "Test error"
        assert result["error_code"] == "TEST_ERROR"
        assert result["status_code"] == 400
        assert result["details"] == {"key": "value"}
        assert "correlation_id" in result
        assert "timestamp" in result

    def test_to_dict_with_cause(self) -> None:
        """Test AppError serialization with cause."""
        cause = AppError(message="Cause error", error_code="CAUSE")
        error = AppError(message="Main error", error_code="MAIN")
        error.__cause__ = cause

        result = error.to_dict()
        assert "cause" in result
        assert result["cause"]["message"] == "Cause error"

    def test_to_dict_with_non_app_cause(self) -> None:
        """Test AppError serialization with non-AppError cause."""
        error = AppError(message="Main error", error_code="MAIN")
        error.__cause__ = ValueError("Original error")

        result = error.to_dict()
        assert "cause" in result
        assert result["cause"]["type"] == "ValueError"
        assert result["cause"]["message"] == "Original error"


class TestAppExceptionAlias:
    """Tests for AppException backwards compatibility alias."""

    def test_alias_is_app_error(self) -> None:
        """Test AppException is alias for AppError."""
        assert AppException is AppError


class TestEntityNotFoundError:
    """Tests for EntityNotFoundError."""

    def test_creation(self) -> None:
        """Test EntityNotFoundError creation."""
        error = EntityNotFoundError(entity_type="User", entity_id="123")

        assert "User" in error.message
        assert "123" in error.message
        assert error.status_code == 404
        assert error.details["entity_type"] == "User"
        assert error.details["entity_id"] == "123"

    def test_with_int_id(self) -> None:
        """Test EntityNotFoundError with integer ID."""
        error = EntityNotFoundError(entity_type="Order", entity_id=456)

        assert "456" in error.message
        assert error.details["entity_id"] == "456"


class TestValidationError:
    """Tests for ValidationError."""

    def test_with_list_errors(self) -> None:
        """Test ValidationError with list of errors."""
        errors = [
            {"field": "email", "message": "Invalid email"},
            {"field": "name", "message": "Required"},
        ]
        error = ValidationError(errors=errors)

        assert error.status_code == 422
        assert error.details["errors"] == errors

    def test_with_dict_errors(self) -> None:
        """Test ValidationError with dict of errors."""
        errors = {"email": "Invalid email", "name": "Required"}
        error = ValidationError(errors=errors)

        assert error.status_code == 422
        assert len(error.details["errors"]) == 2

    def test_custom_message(self) -> None:
        """Test ValidationError with custom message."""
        error = ValidationError(errors=[], message="Custom validation failed")

        assert error.message == "Custom validation failed"

    def test_with_context(self) -> None:
        """Test ValidationError with context."""
        ctx = ErrorContext(request_path="/api/users")
        error = ValidationError(errors=[], context=ctx)

        assert error.context.request_path == "/api/users"


class TestBusinessRuleViolationError:
    """Tests for BusinessRuleViolationError."""

    def test_creation(self) -> None:
        """Test BusinessRuleViolationError creation."""
        error = BusinessRuleViolationError(
            rule="MAX_ITEMS", message="Cannot exceed 100 items"
        )

        assert "MAX_ITEMS" in error.message
        assert "Cannot exceed 100 items" in error.message
        assert error.status_code == 400
        assert error.details["rule"] == "MAX_ITEMS"
        assert "MAX_ITEMS" in error.error_code


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self) -> None:
        """Test AuthenticationError with default message."""
        error = AuthenticationError()

        assert error.status_code == 401
        assert error.details["scheme"] == "Bearer"

    def test_custom_message(self) -> None:
        """Test AuthenticationError with custom message."""
        error = AuthenticationError(message="Token expired")

        assert error.message == "Token expired"

    def test_custom_scheme(self) -> None:
        """Test AuthenticationError with custom scheme."""
        error = AuthenticationError(scheme="Basic")

        assert error.details["scheme"] == "Basic"


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_message(self) -> None:
        """Test AuthorizationError with default message."""
        error = AuthorizationError()

        assert error.status_code == 403

    def test_with_required_permission(self) -> None:
        """Test AuthorizationError with required permission."""
        error = AuthorizationError(required_permission="admin:write")

        assert "admin:write" in error.message
        assert error.details["required_permission"] == "admin:write"

    def test_custom_message(self) -> None:
        """Test AuthorizationError with custom message."""
        error = AuthorizationError(message="Access denied to resource")

        assert error.message == "Access denied to resource"


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError."""

    def test_creation(self) -> None:
        """Test RateLimitExceededError creation."""
        error = RateLimitExceededError(retry_after=60)

        assert error.status_code == 429
        assert error.details["retry_after"] == 60
        assert "60" in error.message

    def test_custom_message(self) -> None:
        """Test RateLimitExceededError with custom message."""
        error = RateLimitExceededError(retry_after=30, message="Too many requests")

        assert error.message == "Too many requests"


class TestConflictError:
    """Tests for ConflictError."""

    def test_default_message(self) -> None:
        """Test ConflictError with default message."""
        error = ConflictError()

        assert error.status_code == 409
        assert error.message == "Resource conflict"

    def test_with_resource_info(self) -> None:
        """Test ConflictError with resource info."""
        error = ConflictError(resource_type="User", resource_id="123")

        assert "User" in error.message
        assert "123" in error.message
        assert error.details["resource_type"] == "User"
        assert error.details["resource_id"] == "123"

    def test_custom_message(self) -> None:
        """Test ConflictError with custom message."""
        error = ConflictError(message="Email already exists")

        assert error.message == "Email already exists"
