"""Unit tests for infrastructure error hierarchy.

Tests InfrastructureError and all derived error classes.
"""

import pytest

from infrastructure.errors import (
    AuditLogError,
    CacheError,
    ConfigurationError,
    ConnectionPoolError,
    DatabaseError,
    ExternalServiceError,
    InfrastructureError,
    MessagingError,
    StorageError,
    TelemetryError,
    TokenStoreError,
    TokenValidationError,
)


class TestInfrastructureError:
    """Tests for InfrastructureError base class."""

    def test_basic_creation(self) -> None:
        """Test basic error creation."""
        error = InfrastructureError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details == {}
        assert str(error) == "Something went wrong"

    def test_with_details(self) -> None:
        """Test error with details."""
        error = InfrastructureError(
            "Operation failed",
            details={"operation": "connect", "host": "localhost"},
        )
        assert error.details["operation"] == "connect"
        assert error.details["host"] == "localhost"
        assert "operation=connect" in str(error)
        assert "host=localhost" in str(error)

    def test_is_exception(self) -> None:
        """Test error is an Exception."""
        error = InfrastructureError("Error")
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(InfrastructureError) as exc_info:
            raise InfrastructureError("Test error")
        assert exc_info.value.message == "Test error"


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_basic_creation(self) -> None:
        """Test basic database error."""
        error = DatabaseError("Query failed")
        assert error.message == "Query failed"
        assert isinstance(error, InfrastructureError)

    def test_with_details(self) -> None:
        """Test database error with details."""
        error = DatabaseError(
            "Connection timeout",
            details={"database": "mydb", "timeout_ms": 5000},
        )
        assert error.details["database"] == "mydb"


class TestConnectionPoolError:
    """Tests for ConnectionPoolError."""

    def test_basic_creation(self) -> None:
        """Test basic connection pool error."""
        error = ConnectionPoolError("Pool exhausted")
        assert error.message == "Pool exhausted"
        assert isinstance(error, DatabaseError)
        assert isinstance(error, InfrastructureError)

    def test_with_details(self) -> None:
        """Test connection pool error with details."""
        error = ConnectionPoolError(
            "No available connections",
            details={"pool_size": 10, "active": 10},
        )
        assert error.details["pool_size"] == 10


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_basic_creation(self) -> None:
        """Test basic external service error."""
        error = ExternalServiceError("Service unavailable")
        assert error.message == "Service unavailable"
        assert error.service_name is None
        assert error.retry_after is None

    def test_with_service_name(self) -> None:
        """Test external service error with service name."""
        error = ExternalServiceError(
            "API call failed",
            service_name="payment-gateway",
        )
        assert error.service_name == "payment-gateway"

    def test_with_retry_after(self) -> None:
        """Test external service error with retry_after."""
        error = ExternalServiceError(
            "Rate limited",
            service_name="api",
            retry_after=60,
        )
        assert error.retry_after == 60

    def test_inherits_infrastructure_error(self) -> None:
        """Test inherits from InfrastructureError."""
        error = ExternalServiceError("Error")
        assert isinstance(error, InfrastructureError)


class TestCacheError:
    """Tests for CacheError."""

    def test_basic_creation(self) -> None:
        """Test basic cache error."""
        error = CacheError("Cache miss")
        assert error.message == "Cache miss"
        assert isinstance(error, InfrastructureError)

    def test_with_details(self) -> None:
        """Test cache error with details."""
        error = CacheError(
            "Redis connection failed",
            details={"host": "redis", "port": 6379},
        )
        assert error.details["host"] == "redis"


class TestMessagingError:
    """Tests for MessagingError."""

    def test_basic_creation(self) -> None:
        """Test basic messaging error."""
        error = MessagingError("Message publish failed")
        assert error.message == "Message publish failed"
        assert isinstance(error, InfrastructureError)


class TestStorageError:
    """Tests for StorageError."""

    def test_basic_creation(self) -> None:
        """Test basic storage error."""
        error = StorageError("File upload failed")
        assert error.message == "File upload failed"
        assert isinstance(error, InfrastructureError)


class TestTokenStoreError:
    """Tests for TokenStoreError."""

    def test_basic_creation(self) -> None:
        """Test basic token store error."""
        error = TokenStoreError("Token storage failed")
        assert error.message == "Token storage failed"
        assert isinstance(error, InfrastructureError)


class TestTokenValidationError:
    """Tests for TokenValidationError."""

    def test_basic_creation(self) -> None:
        """Test basic token validation error."""
        error = TokenValidationError("Invalid token signature")
        assert error.message == "Invalid token signature"
        assert isinstance(error, TokenStoreError)
        assert isinstance(error, InfrastructureError)


class TestAuditLogError:
    """Tests for AuditLogError."""

    def test_basic_creation(self) -> None:
        """Test basic audit log error."""
        error = AuditLogError("Audit log write failed")
        assert error.message == "Audit log write failed"
        assert isinstance(error, InfrastructureError)


class TestTelemetryError:
    """Tests for TelemetryError."""

    def test_basic_creation(self) -> None:
        """Test basic telemetry error."""
        error = TelemetryError("Metric export failed")
        assert error.message == "Metric export failed"
        assert isinstance(error, InfrastructureError)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_basic_creation(self) -> None:
        """Test basic configuration error."""
        error = ConfigurationError("Missing required config")
        assert error.message == "Missing required config"
        assert isinstance(error, InfrastructureError)

    def test_with_details(self) -> None:
        """Test configuration error with details."""
        error = ConfigurationError(
            "Invalid configuration",
            details={"key": "DATABASE_URL", "reason": "missing"},
        )
        assert error.details["key"] == "DATABASE_URL"
