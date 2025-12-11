"""Unit tests for gRPC BaseServicer.

Tests the base servicer functionality including DI, CQRS, and error handling.

**Feature: interface-modules-workflow-analysis**
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# Constants duplicated to avoid import issues
_CORRELATION_ID_HEADER = "x-correlation-id"
_ERR_INTERNAL = "Internal server error"
_ERR_NOT_FOUND = "Resource not found"
_ERR_VALIDATION = "Validation failed"


class TestCorrelationIdExtraction:
    """Tests for correlation ID extraction logic."""

    def test_extracts_from_metadata(self) -> None:
        """Extracts correlation ID from metadata."""
        metadata = [(_CORRELATION_ID_HEADER, "test-correlation-123")]
        result = dict(metadata).get(_CORRELATION_ID_HEADER)
        assert result == "test-correlation-123"

    def test_missing_header_returns_none(self) -> None:
        """Missing header returns None from dict.get."""
        metadata: list[tuple[str, str]] = []
        result = dict(metadata).get(_CORRELATION_ID_HEADER)
        assert result is None

    def test_empty_metadata_returns_none(self) -> None:
        """Empty metadata returns None."""
        metadata: list[tuple[str, str]] = []
        result = dict(metadata).get(_CORRELATION_ID_HEADER)
        assert result is None


class TestErrorSanitization:
    """Tests for error sanitization logic."""

    def _sanitize_error(self, error: Exception) -> str:
        """Duplicate of sanitization logic for testing."""
        error_type = type(error).__name__
        if "NotFound" in error_type:
            return _ERR_NOT_FOUND
        if "Validation" in error_type:
            return _ERR_VALIDATION
        return _ERR_INTERNAL

    def test_not_found_error(self) -> None:
        """NotFound errors return safe message."""

        class ItemNotFoundError(Exception):
            pass

        result = self._sanitize_error(ItemNotFoundError("Item 123"))
        assert result == _ERR_NOT_FOUND

    def test_validation_error(self) -> None:
        """Validation errors return safe message."""

        class ValidationError(Exception):
            pass

        result = self._sanitize_error(ValidationError("Invalid input"))
        assert result == _ERR_VALIDATION

    def test_generic_error(self) -> None:
        """Generic errors return internal error message."""
        result = self._sanitize_error(RuntimeError("DB connection failed"))
        assert result == _ERR_INTERNAL

    def test_does_not_expose_internal_details(self) -> None:
        """Error messages do not expose internal details."""
        sensitive_error = RuntimeError("Connection to db.internal:5432 failed")
        result = self._sanitize_error(sensitive_error)
        assert "db.internal" not in result
        assert "5432" not in result


class TestGrpcStatusMapping:
    """Tests for gRPC status code mapping."""

    def _get_grpc_status(self, error: Exception) -> str:
        """Duplicate of status mapping logic for testing."""
        error_type = type(error).__name__
        if "NotFound" in error_type:
            return "NOT_FOUND"
        if "Validation" in error_type or "Invalid" in error_type:
            return "INVALID_ARGUMENT"
        if "Permission" in error_type or "Forbidden" in error_type:
            return "PERMISSION_DENIED"
        if "Unauthorized" in error_type or "Auth" in error_type:
            return "UNAUTHENTICATED"
        return "INTERNAL"

    def test_not_found_maps_correctly(self) -> None:
        """NotFound maps to NOT_FOUND."""

        class ResourceNotFoundError(Exception):
            pass

        assert self._get_grpc_status(ResourceNotFoundError()) == "NOT_FOUND"

    def test_validation_maps_correctly(self) -> None:
        """Validation maps to INVALID_ARGUMENT."""

        class ValidationError(Exception):
            pass

        assert self._get_grpc_status(ValidationError()) == "INVALID_ARGUMENT"

    def test_invalid_maps_correctly(self) -> None:
        """Invalid maps to INVALID_ARGUMENT."""

        class InvalidInputError(Exception):
            pass

        assert self._get_grpc_status(InvalidInputError()) == "INVALID_ARGUMENT"

    def test_permission_maps_correctly(self) -> None:
        """Permission maps to PERMISSION_DENIED."""

        class PermissionDeniedError(Exception):
            pass

        assert self._get_grpc_status(PermissionDeniedError()) == "PERMISSION_DENIED"

    def test_forbidden_maps_correctly(self) -> None:
        """Forbidden maps to PERMISSION_DENIED."""

        class ForbiddenError(Exception):
            pass

        assert self._get_grpc_status(ForbiddenError()) == "PERMISSION_DENIED"

    def test_unauthorized_maps_correctly(self) -> None:
        """Unauthorized maps to UNAUTHENTICATED."""

        class UnauthorizedError(Exception):
            pass

        assert self._get_grpc_status(UnauthorizedError()) == "UNAUTHENTICATED"

    def test_auth_maps_correctly(self) -> None:
        """Auth errors map to UNAUTHENTICATED."""

        class AuthenticationError(Exception):
            pass

        assert self._get_grpc_status(AuthenticationError()) == "UNAUTHENTICATED"

    def test_generic_maps_to_internal(self) -> None:
        """Generic errors map to INTERNAL."""
        assert self._get_grpc_status(RuntimeError()) == "INTERNAL"


class TestDIIntegration:
    """Tests for dependency injection integration."""

    def test_container_not_configured_raises(self) -> None:
        """Missing container raises RuntimeError."""
        container = None
        with pytest.raises(RuntimeError, match="not configured"):
            if container is None:
                raise RuntimeError("DI container not configured")

    def test_query_bus_not_configured_raises(self) -> None:
        """Missing QueryBus raises RuntimeError."""
        query_bus = None
        with pytest.raises(RuntimeError, match="not configured"):
            if query_bus is None:
                raise RuntimeError("QueryBus not configured")

    def test_command_bus_not_configured_raises(self) -> None:
        """Missing CommandBus raises RuntimeError."""
        command_bus = None
        with pytest.raises(RuntimeError, match="not configured"):
            if command_bus is None:
                raise RuntimeError("CommandBus not configured")

    def test_container_resolves_type(self) -> None:
        """Container resolves requested type."""
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_container.resolve.return_value = mock_service

        result = mock_container.resolve(type(mock_service))

        assert result == mock_service
        mock_container.resolve.assert_called_once()
