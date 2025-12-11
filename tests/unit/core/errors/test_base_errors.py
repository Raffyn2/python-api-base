"""Unit tests for base error classes.

Tests error hierarchy, context, and serialization.
"""

from datetime import datetime

import pytest

from core.errors import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    EntityNotFoundError,
    ErrorContext,
    RateLimitExceededError,
    ValidationError,
)
from core.errors.base.infrastructure_errors import (
    CacheError,
    ConfigurationError,
    DatabaseError,
    ExternalServiceError,
    InfrastructureError,
    TokenStoreError,
)


class TestErrorContext:
    """Tests for ErrorContext dataclass."""

    def test_basic_creation_with_defaults(self) -> None:
        """Test ErrorContext creation with default values."""
        ctx = ErrorContext()
        assert ctx.correlation_id is not None
        assert ctx.timestamp is not None
        assert ctx.request_path is None

    def test_with_request_path(self) -> None:
        """Test ErrorContext with request_path."""
        ctx = ErrorContext(request_path="/api/users")
        assert ctx.request_path == "/api/users"

    def test_to_dict(self) -> None:
        """Test ErrorContext serialization."""
        ctx = ErrorContext(request_path="/api/items")
        data = ctx.to_dict()
        assert "correlation_id" in data
        assert "timestamp" in data
        assert data["request_path"] == "/api/items"

    def test_immutability(self) -> None:
        """Test ErrorContext is immutable (frozen)."""
        ctx = ErrorContext()
        with pytest.raises(AttributeError):
            ctx.correlation_id = "new-id"


class TestAppError:
    """Tests for AppError base class."""

    def test_basic_creation(self) -> None:
        """Test basic AppError creation."""
        error = AppError(
            message="Something went wrong",
            error_code="ERR_001",
        )
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.error_code == "ERR_001"
        assert error.status_code == 400

    def test_with_status_code(self) -> None:
        """Test AppError with custom status code."""
        error = AppError(
            message="Not found",
            error_code="NOT_FOUND",
            status_code=404,
        )
        assert error.status_code == 404

    def test_with_details(self) -> None:
        """Test AppError with details."""
        error = AppError(
            message="Error",
            error_code="ERR",
            details={"field": "email"},
        )
        assert error.details["field"] == "email"

    def test_with_context(self) -> None:
        """Test AppError with context."""
        ctx = ErrorContext(request_path="/test")
        error = AppError(
            message="Error",
            error_code="ERR",
            context=ctx,
        )
        assert error.context == ctx
        assert error.context.request_path == "/test"

    def test_correlation_id_property(self) -> None:
        """Test correlation_id property."""
        error = AppError(message="Error", error_code="ERR")
        assert error.correlation_id == error.context.correlation_id

    def test_timestamp_property(self) -> None:
        """Test timestamp property."""
        error = AppError(message="Error", error_code="ERR")
        assert isinstance(error.timestamp, datetime)

    def test_to_dict(self) -> None:
        """Test AppError serialization."""
        error = AppError(
            message="Test error",
            error_code="TEST_ERR",
            status_code=500,
            details={"key": "value"},
        )
        data = error.to_dict()
        assert data["message"] == "Test error"
        assert data["error_code"] == "TEST_ERR"
        assert data["status_code"] == 500
        assert data["details"]["key"] == "value"
        assert "correlation_id" in data
        assert "timestamp" in data

    def test_to_dict_with_cause(self) -> None:
        """Test AppError serialization with cause."""
        cause = ValueError("Original error")
        error = AppError(message="Wrapped", error_code="WRAP")
        error.__cause__ = cause
        data = error.to_dict()
        assert "cause" in data
        assert data["cause"]["type"] == "ValueError"


class TestValidationError:
    """Tests for ValidationError."""

    def test_with_list_errors(self) -> None:
        """Test ValidationError with list of errors."""
        errors = [{"field": "email", "message": "Invalid format"}]
        error = ValidationError(errors=errors)
        assert error.status_code == 422
        assert "errors" in error.details

    def test_with_dict_errors(self) -> None:
        """Test ValidationError with dict errors (normalized to list)."""
        errors = {"email": "Invalid format", "name": "Required"}
        error = ValidationError(errors=errors)
        assert error.status_code == 422
        normalized = error.details["errors"]
        assert len(normalized) == 2

    def test_with_custom_message(self) -> None:
        """Test ValidationError with custom message."""
        error = ValidationError(
            errors=[],
            message="Custom validation message",
        )
        assert error.message == "Custom validation message"


class TestEntityNotFoundError:
    """Tests for EntityNotFoundError."""

    def test_basic_creation(self) -> None:
        """Test basic EntityNotFoundError creation."""
        error = EntityNotFoundError("User", "123")
        assert "User" in str(error)
        assert "123" in str(error)
        assert error.status_code == 404

    def test_details_contain_entity_info(self) -> None:
        """Test details contain entity type and id."""
        error = EntityNotFoundError("Order", "456")
        assert error.details["entity_type"] == "Order"
        assert error.details["entity_id"] == "456"

    def test_with_int_id(self) -> None:
        """Test EntityNotFoundError with integer id."""
        error = EntityNotFoundError("Product", 789)
        assert error.details["entity_id"] == "789"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self) -> None:
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert error.status_code == 401
        assert "scheme" in error.details

    def test_custom_message(self) -> None:
        """Test AuthenticationError with custom message."""
        error = AuthenticationError(message="Invalid token")
        assert "Invalid token" in str(error)

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
        assert error.details["required_permission"] == "admin:write"


class TestConflictError:
    """Tests for ConflictError."""

    def test_default_message(self) -> None:
        """Test ConflictError with default message."""
        error = ConflictError()
        assert error.status_code == 409

    def test_with_resource_info(self) -> None:
        """Test ConflictError with resource info."""
        error = ConflictError(
            resource_type="User",
            resource_id="123",
        )
        assert error.details["resource_type"] == "User"
        assert error.details["resource_id"] == "123"

    def test_custom_message(self) -> None:
        """Test ConflictError with custom message."""
        error = ConflictError(message="Email already exists")
        assert "Email already exists" in str(error)


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError."""

    def test_basic_creation(self) -> None:
        """Test RateLimitExceededError creation."""
        error = RateLimitExceededError(retry_after=60)
        assert error.status_code == 429
        assert error.details["retry_after"] == 60

    def test_custom_message(self) -> None:
        """Test RateLimitExceededError with custom message."""
        error = RateLimitExceededError(
            retry_after=30,
            message="Too many requests",
        )
        assert "Too many requests" in str(error)


class TestInfrastructureError:
    """Tests for InfrastructureError base class."""

    def test_basic_creation(self) -> None:
        """Test basic InfrastructureError creation."""
        error = InfrastructureError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.message == "Connection failed"

    def test_with_details(self) -> None:
        """Test InfrastructureError with details."""
        error = InfrastructureError(
            "Query failed",
            details={"query": "SELECT *", "table": "users"},
        )
        assert "query=SELECT *" in str(error)
        assert error.details["table"] == "users"


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_basic_creation(self) -> None:
        """Test DatabaseError creation."""
        error = DatabaseError("Connection pool exhausted")
        assert "Connection pool exhausted" in str(error)

    def test_inherits_infrastructure_error(self) -> None:
        """Test DatabaseError inherits from InfrastructureError."""
        error = DatabaseError("Error")
        assert isinstance(error, InfrastructureError)


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_basic_creation(self) -> None:
        """Test ExternalServiceError creation."""
        error = ExternalServiceError(
            message="API timeout",
            service_name="payment-gateway",
        )
        assert "API timeout" in str(error)
        assert error.service_name == "payment-gateway"

    def test_with_retry_after(self) -> None:
        """Test ExternalServiceError with retry_after."""
        error = ExternalServiceError(
            message="Rate limited",
            service_name="external-api",
            retry_after=120,
        )
        assert error.retry_after == 120


class TestCacheError:
    """Tests for CacheError."""

    def test_basic_creation(self) -> None:
        """Test CacheError creation."""
        error = CacheError("Redis connection failed")
        assert "Redis connection failed" in str(error)
        assert isinstance(error, InfrastructureError)


class TestTokenStoreError:
    """Tests for TokenStoreError."""

    def test_basic_creation(self) -> None:
        """Test TokenStoreError creation."""
        error = TokenStoreError("Token storage failed")
        assert "Token storage failed" in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_basic_creation(self) -> None:
        """Test ConfigurationError creation."""
        error = ConfigurationError("Missing DATABASE_URL")
        assert "Missing DATABASE_URL" in str(error)
