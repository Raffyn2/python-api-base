"""Tests for infrastructure error classes.

Tests InfrastructureError and all derived error types.
"""

import pytest

from infrastructure.errors.base import InfrastructureError
from infrastructure.errors.database import ConnectionPoolError, DatabaseError
from infrastructure.errors.external import (
    CacheError,
    ExternalServiceError,
    MessagingError,
    StorageError,
)
from infrastructure.errors.security import (
    AuditLogError,
    TokenStoreError,
    TokenValidationError,
)
from infrastructure.errors.system import ConfigurationError, TelemetryError


class TestInfrastructureError:
    """Tests for InfrastructureError base class."""

    def test_create_with_message_only(self) -> None:
        error = InfrastructureError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details == {}
        assert str(error) == "Something went wrong"

    def test_create_with_details(self) -> None:
        error = InfrastructureError(
            "Operation failed",
            details={"operation": "read", "resource": "users"},
        )
        assert error.message == "Operation failed"
        assert error.details == {"operation": "read", "resource": "users"}

    def test_format_message_with_details(self) -> None:
        error = InfrastructureError(
            "Error occurred",
            details={"key": "value"},
        )
        assert "key=value" in str(error)

    def test_is_exception(self) -> None:
        error = InfrastructureError("Test")
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        with pytest.raises(InfrastructureError) as exc_info:
            raise InfrastructureError("Test error")
        assert "Test error" in str(exc_info.value)


class TestDatabaseErrors:
    """Tests for database error classes."""

    def test_database_error(self) -> None:
        error = DatabaseError("Query failed", details={"query_id": "123"})
        assert isinstance(error, InfrastructureError)
        assert error.message == "Query failed"

    def test_connection_pool_error(self) -> None:
        error = ConnectionPoolError(
            "Pool exhausted",
            details={"pool_size": 10, "active": 10},
        )
        assert isinstance(error, DatabaseError)
        assert isinstance(error, InfrastructureError)
        assert "Pool exhausted" in str(error)

    def test_database_error_inheritance(self) -> None:
        error = ConnectionPoolError("Test")
        with pytest.raises(DatabaseError):
            raise error
        with pytest.raises(InfrastructureError):
            raise error


class TestExternalServiceErrors:
    """Tests for external service error classes."""

    def test_external_service_error_basic(self) -> None:
        error = ExternalServiceError("Service unavailable")
        assert error.message == "Service unavailable"
        assert error.service_name is None
        assert error.retry_after is None

    def test_external_service_error_with_service_name(self) -> None:
        error = ExternalServiceError(
            "API call failed",
            service_name="payment-gateway",
        )
        assert error.service_name == "payment-gateway"

    def test_external_service_error_with_retry_after(self) -> None:
        error = ExternalServiceError(
            "Rate limited",
            service_name="api",
            retry_after=60,
        )
        assert error.retry_after == 60

    def test_external_service_error_with_details(self) -> None:
        error = ExternalServiceError(
            "Request failed",
            service_name="external-api",
            retry_after=30,
            details={"status_code": 503},
        )
        assert error.details == {"status_code": 503}

    def test_cache_error(self) -> None:
        error = CacheError("Cache miss", details={"key": "user:123"})
        assert isinstance(error, InfrastructureError)
        assert error.message == "Cache miss"

    def test_messaging_error(self) -> None:
        error = MessagingError(
            "Failed to publish",
            details={"topic": "events", "partition": 0},
        )
        assert isinstance(error, InfrastructureError)
        assert "Failed to publish" in str(error)

    def test_storage_error(self) -> None:
        error = StorageError(
            "File not found",
            details={"path": "/data/file.txt"},
        )
        assert isinstance(error, InfrastructureError)
        assert error.message == "File not found"


class TestSecurityErrors:
    """Tests for security error classes."""

    def test_token_store_error(self) -> None:
        error = TokenStoreError(
            "Failed to store token",
            details={"user_id": "user-123"},
        )
        assert isinstance(error, InfrastructureError)
        assert error.message == "Failed to store token"

    def test_token_validation_error(self) -> None:
        error = TokenValidationError(
            "Token expired",
            details={"token_type": "access"},
        )
        assert isinstance(error, TokenStoreError)
        assert isinstance(error, InfrastructureError)

    def test_token_validation_error_inheritance(self) -> None:
        error = TokenValidationError("Invalid signature")
        with pytest.raises(TokenStoreError):
            raise error

    def test_audit_log_error(self) -> None:
        error = AuditLogError(
            "Failed to write audit log",
            details={"event_type": "user_login"},
        )
        assert isinstance(error, InfrastructureError)
        assert "Failed to write audit log" in str(error)


class TestSystemErrors:
    """Tests for system error classes."""

    def test_telemetry_error(self) -> None:
        error = TelemetryError(
            "Failed to export metrics",
            details={"exporter": "prometheus"},
        )
        assert isinstance(error, InfrastructureError)
        assert error.message == "Failed to export metrics"

    def test_configuration_error(self) -> None:
        error = ConfigurationError(
            "Missing required config",
            details={"key": "DATABASE_URL"},
        )
        assert isinstance(error, InfrastructureError)
        assert "Missing required config" in str(error)


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_all_errors_inherit_from_infrastructure_error(self) -> None:
        error_classes = [
            DatabaseError,
            ConnectionPoolError,
            ExternalServiceError,
            CacheError,
            MessagingError,
            StorageError,
            TokenStoreError,
            TokenValidationError,
            AuditLogError,
            TelemetryError,
            ConfigurationError,
        ]

        for error_class in error_classes:
            error = error_class("Test")
            assert isinstance(error, InfrastructureError), (
                f"{error_class.__name__} should inherit from InfrastructureError"
            )

    def test_catch_all_infrastructure_errors(self) -> None:
        """Verify all errors can be caught with InfrastructureError."""
        errors = [
            DatabaseError("db error"),
            CacheError("cache error"),
            TokenStoreError("token error"),
            TelemetryError("telemetry error"),
        ]

        for error in errors:
            try:
                raise error
            except InfrastructureError as e:
                assert e.message is not None
