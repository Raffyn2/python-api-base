"""Unit tests for infrastructure error classes.

**Task: Phase 4 - Infrastructure Layer Tests**
**Requirements: 4.3**
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
        """Error should be created with message only."""
        error = InfrastructureError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_create_with_details(self) -> None:
        """Error should accept details dict."""
        error = InfrastructureError(
            "Operation failed",
            details={"operation": "read", "resource": "users"},
        )
        assert error.message == "Operation failed"
        assert error.details == {"operation": "read", "resource": "users"}

    def test_is_exception(self) -> None:
        """Error should be an Exception."""
        error = InfrastructureError("Test")
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Error should be raisable."""
        with pytest.raises(InfrastructureError):
            raise InfrastructureError("Test error")


class TestDatabaseErrors:
    """Tests for database error classes."""

    def test_database_error(self) -> None:
        """DatabaseError should inherit from InfrastructureError."""
        error = DatabaseError("Query failed")
        assert isinstance(error, InfrastructureError)
        assert error.message == "Query failed"

    def test_connection_pool_error(self) -> None:
        """ConnectionPoolError should inherit from DatabaseError."""
        error = ConnectionPoolError("Pool exhausted")
        assert isinstance(error, DatabaseError)
        assert isinstance(error, InfrastructureError)


class TestExternalServiceErrors:
    """Tests for external service error classes."""

    def test_external_service_error(self) -> None:
        """ExternalServiceError should have service info."""
        error = ExternalServiceError("Service unavailable")
        assert isinstance(error, InfrastructureError)

    def test_cache_error(self) -> None:
        """CacheError should inherit from InfrastructureError."""
        error = CacheError("Cache miss")
        assert isinstance(error, InfrastructureError)

    def test_messaging_error(self) -> None:
        """MessagingError should inherit from InfrastructureError."""
        error = MessagingError("Failed to publish")
        assert isinstance(error, InfrastructureError)

    def test_storage_error(self) -> None:
        """StorageError should inherit from InfrastructureError."""
        error = StorageError("File not found")
        assert isinstance(error, InfrastructureError)


class TestSecurityErrors:
    """Tests for security error classes."""

    def test_token_store_error(self) -> None:
        """TokenStoreError should inherit from InfrastructureError."""
        error = TokenStoreError("Failed to store token")
        assert isinstance(error, InfrastructureError)

    def test_token_validation_error(self) -> None:
        """TokenValidationError should inherit from TokenStoreError."""
        error = TokenValidationError("Token expired")
        assert isinstance(error, TokenStoreError)

    def test_audit_log_error(self) -> None:
        """AuditLogError should inherit from InfrastructureError."""
        error = AuditLogError("Failed to write audit log")
        assert isinstance(error, InfrastructureError)


class TestSystemErrors:
    """Tests for system error classes."""

    def test_telemetry_error(self) -> None:
        """TelemetryError should inherit from InfrastructureError."""
        error = TelemetryError("Failed to export metrics")
        assert isinstance(error, InfrastructureError)

    def test_configuration_error(self) -> None:
        """ConfigurationError should inherit from InfrastructureError."""
        error = ConfigurationError("Missing required config")
        assert isinstance(error, InfrastructureError)


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_all_errors_inherit_from_infrastructure_error(self) -> None:
        """All error classes should inherit from InfrastructureError."""
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
            assert isinstance(error, InfrastructureError)
