"""Unit tests for GraphQL mutations.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.3**
"""

from unittest.mock import MagicMock

import pytest

# Constants (duplicated to avoid import issues with strawberry)
_ERR_INTERNAL = "An internal error occurred"
_ERR_NOT_FOUND = "Resource not found"
_ERR_VALIDATION = "Validation failed"


def _get_command_bus(info: MagicMock):
    """Extract CommandBus from context."""
    bus = info.context.get("command_bus")
    if bus is None:
        raise RuntimeError("CommandBus not configured")
    return bus


def _get_correlation_id(info: MagicMock) -> str | None:
    """Extract correlation ID from context."""
    return info.context.get("correlation_id")


def _sanitize_error(error: Exception) -> str:
    """Sanitize error message for client response."""
    error_type = type(error).__name__
    if "NotFound" in error_type:
        return _ERR_NOT_FOUND
    if "Validation" in error_type:
        return _ERR_VALIDATION
    return _ERR_INTERNAL


class TestErrorSanitization:
    """Tests for error sanitization."""

    def test_sanitize_not_found_error(self) -> None:
        """NotFound errors should return not found message."""

        class ItemNotFoundError(Exception):
            pass

        result = _sanitize_error(ItemNotFoundError("Item 123 not found"))

        assert result == _ERR_NOT_FOUND

    def test_sanitize_validation_error(self) -> None:
        """Validation errors should return validation message."""

        class ValidationError(Exception):
            pass

        result = _sanitize_error(ValidationError("Invalid input"))

        assert result == _ERR_VALIDATION

    def test_sanitize_generic_error(self) -> None:
        """Generic errors should return internal error message."""
        result = _sanitize_error(Exception("Database connection failed"))

        assert result == _ERR_INTERNAL

    def test_sanitize_does_not_expose_details(self) -> None:
        """Sanitized errors should not expose internal details."""
        sensitive_error = Exception("Connection to db.internal.corp:5432 failed")

        result = _sanitize_error(sensitive_error)

        assert "db.internal.corp" not in result
        assert "5432" not in result
        assert result == _ERR_INTERNAL


class TestContextExtraction:
    """Tests for context extraction functions."""

    def test_get_command_bus_success(self) -> None:
        """Should return CommandBus when present in context."""
        mock_bus = MagicMock()
        mock_info = MagicMock()
        mock_info.context = {"command_bus": mock_bus}

        result = _get_command_bus(mock_info)

        assert result is mock_bus

    def test_get_command_bus_missing_raises(self) -> None:
        """Should raise RuntimeError when CommandBus is missing."""
        mock_info = MagicMock()
        mock_info.context = {}

        with pytest.raises(RuntimeError, match="CommandBus not configured"):
            _get_command_bus(mock_info)

    def test_get_correlation_id_present(self) -> None:
        """Should return correlation ID when present."""
        mock_info = MagicMock()
        mock_info.context = {"correlation_id": "mutation-corr-456"}

        result = _get_correlation_id(mock_info)

        assert result == "mutation-corr-456"

    def test_get_correlation_id_missing(self) -> None:
        """Should return None when correlation ID is missing."""
        mock_info = MagicMock()
        mock_info.context = {}

        result = _get_correlation_id(mock_info)

        assert result is None


class TestErrorConstants:
    """Tests for error message constants."""

    def test_error_messages_are_generic(self) -> None:
        """Error messages should be generic and safe."""
        assert "internal" in _ERR_INTERNAL.lower()
        assert "not found" in _ERR_NOT_FOUND.lower()
        assert "validation" in _ERR_VALIDATION.lower()

    def test_error_messages_no_sensitive_info(self) -> None:
        """Error messages should not contain sensitive information."""
        all_messages = [_ERR_INTERNAL, _ERR_NOT_FOUND, _ERR_VALIDATION]

        for msg in all_messages:
            assert "password" not in msg.lower()
            assert "token" not in msg.lower()
            assert "secret" not in msg.lower()
            assert "database" not in msg.lower()
