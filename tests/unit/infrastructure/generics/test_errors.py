"""Unit tests for generics errors module.

Tests ErrorMessages and typed error classes.
"""

from infrastructure.generics.core.errors import (
    AuthenticationError,
    CacheError,
    ErrorMessages,
    InfrastructureError,
    MessagingError,
    PoolError,
    SecurityError,
    ValidationError,
)


class TestErrorMessages:
    """Tests for ErrorMessages constants."""

    def test_auth_token_expired(self) -> None:
        """Test AUTH_TOKEN_EXPIRED message."""
        assert ErrorMessages.AUTH_TOKEN_EXPIRED == "Token has expired"

    def test_auth_token_invalid(self) -> None:
        """Test AUTH_TOKEN_INVALID message."""
        assert ErrorMessages.AUTH_TOKEN_INVALID == "Invalid token"

    def test_cache_key_not_found(self) -> None:
        """Test CACHE_KEY_NOT_FOUND message."""
        assert "Cache key not found" in ErrorMessages.CACHE_KEY_NOT_FOUND

    def test_pool_exhausted(self) -> None:
        """Test POOL_EXHAUSTED message."""
        assert ErrorMessages.POOL_EXHAUSTED == "Connection pool exhausted"

    def test_validation_required(self) -> None:
        """Test VALIDATION_REQUIRED message."""
        assert "is required" in ErrorMessages.VALIDATION_REQUIRED

    def test_security_unauthorized(self) -> None:
        """Test SECURITY_UNAUTHORIZED message."""
        assert ErrorMessages.SECURITY_UNAUTHORIZED == "Unauthorized access"

    def test_format_method(self) -> None:
        """Test format method."""
        message = ErrorMessages.format(
            ErrorMessages.CACHE_KEY_NOT_FOUND,
            key="test-key",
        )
        assert "test-key" in message

    def test_format_with_multiple_params(self) -> None:
        """Test format with multiple parameters."""
        message = ErrorMessages.format(
            ErrorMessages.VALIDATION_OUT_OF_RANGE,
            field="age",
            min=0,
            max=120,
        )
        assert "age" in message
        assert "0" in message
        assert "120" in message


class TestInfrastructureError:
    """Tests for InfrastructureError base class."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""
        error = InfrastructureError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.error_code == "INFRASTRUCTURE_ERROR"
        assert error.details == {}

    def test_with_error_code(self) -> None:
        """Test error with custom error code."""
        error = InfrastructureError(
            "Failed",
            error_code="CUSTOM_ERROR",
        )
        assert error.error_code == "CUSTOM_ERROR"

    def test_with_details(self) -> None:
        """Test error with details."""
        error = InfrastructureError(
            "Failed",
            details={"operation": "connect"},
        )
        assert error.details["operation"] == "connect"

    def test_str_format(self) -> None:
        """Test string representation."""
        error = InfrastructureError("Test error", error_code="TEST")
        assert str(error) == "[TEST] Test error"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = AuthenticationError()
        assert error.message == ErrorMessages.AUTH_TOKEN_INVALID
        assert error.error_code == "AUTH_ERROR"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = AuthenticationError("Custom auth error")
        assert error.message == "Custom auth error"

    def test_inherits_infrastructure_error(self) -> None:
        """Test inherits from InfrastructureError."""
        error = AuthenticationError()
        assert isinstance(error, InfrastructureError)


class TestCacheError:
    """Tests for CacheError."""

    def test_basic_creation(self) -> None:
        """Test basic cache error."""
        error = CacheError("Cache miss")
        assert error.message == "Cache miss"
        assert error.error_code == "CACHE_ERROR"

    def test_inherits_infrastructure_error(self) -> None:
        """Test inherits from InfrastructureError."""
        error = CacheError("Error")
        assert isinstance(error, InfrastructureError)


class TestPoolError:
    """Tests for PoolError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = PoolError()
        assert error.message == ErrorMessages.POOL_EXHAUSTED
        assert error.error_code == "POOL_ERROR"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = PoolError("Custom pool error")
        assert error.message == "Custom pool error"


class TestValidationError:
    """Tests for ValidationError."""

    def test_basic_creation(self) -> None:
        """Test basic validation error."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field is None

    def test_with_field(self) -> None:
        """Test validation error with field."""
        error = ValidationError("Invalid email", field="email")
        assert error.field == "email"


class TestSecurityError:
    """Tests for SecurityError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = SecurityError()
        assert error.message == ErrorMessages.SECURITY_UNAUTHORIZED
        assert error.error_code == "SECURITY_ERROR"


class TestMessagingError:
    """Tests for MessagingError."""

    def test_basic_creation(self) -> None:
        """Test basic messaging error."""
        error = MessagingError("Publish failed")
        assert error.message == "Publish failed"
        assert error.error_code == "MESSAGING_ERROR"
