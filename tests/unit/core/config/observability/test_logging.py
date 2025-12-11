"""Unit tests for logging configuration.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 4.1, 5.1, 5.2**
"""

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from core.config.observability.logging import (
    add_request_id,
    add_trace_context,
    clear_request_id,
    configure_logging,
    get_logger,
    get_request_id,
    redact_pii,
    set_request_id,
)


class TestRequestIdContext:
    """Tests for request ID context management."""

    def test_get_request_id_default_none(self) -> None:
        """Test default request ID is None."""
        clear_request_id()
        assert get_request_id() is None

    def test_set_and_get_request_id(self) -> None:
        """Test setting and getting request ID."""
        set_request_id("test-request-123")
        assert get_request_id() == "test-request-123"
        clear_request_id()

    def test_clear_request_id(self) -> None:
        """Test clearing request ID."""
        set_request_id("test-request-456")
        clear_request_id()
        assert get_request_id() is None


class TestAddRequestId:
    """Tests for add_request_id processor."""

    def test_adds_request_id_when_set(self) -> None:
        """Test request ID is added to event dict when set."""
        set_request_id("req-789")
        event_dict: dict[str, Any] = {"event": "test"}

        result = add_request_id(MagicMock(), "info", event_dict)

        assert result["request_id"] == "req-789"
        clear_request_id()

    def test_no_request_id_when_not_set(self) -> None:
        """Test no request ID added when not set."""
        clear_request_id()
        event_dict: dict[str, Any] = {"event": "test"}

        result = add_request_id(MagicMock(), "info", event_dict)

        assert "request_id" not in result


class TestAddTraceContext:
    """Tests for add_trace_context processor."""

    def test_handles_import_error_gracefully(self) -> None:
        """Test graceful handling when tracing module not available."""
        event_dict: dict[str, Any] = {"event": "test"}

        # Should not raise even if tracing module has issues
        result = add_trace_context(MagicMock(), "info", event_dict)

        assert "event" in result


class TestRedactPii:
    """Tests for PII redaction processor."""

    def test_redacts_password_field(self) -> None:
        """Test password fields are redacted."""
        event_dict: dict[str, Any] = {"password": "secret123", "event": "login"}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["password"] == "[REDACTED]"
        assert result["event"] == "login"

    def test_redacts_token_field(self) -> None:
        """Test token fields are redacted."""
        event_dict: dict[str, Any] = {"auth_token": "abc123", "user": "john"}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["auth_token"] == "[REDACTED]"
        assert result["user"] == "john"

    def test_redacts_api_key_field(self) -> None:
        """Test API key fields are redacted."""
        event_dict: dict[str, Any] = {"api_key": "key123", "endpoint": "/api"}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["api_key"] == "[REDACTED]"

    def test_redacts_nested_dict(self) -> None:
        """Test PII in nested dicts is redacted."""
        event_dict: dict[str, Any] = {"data": {"password": "secret", "name": "John"}}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["data"]["password"] == "[REDACTED]"
        assert result["data"]["name"] == "John"

    def test_redacts_list_values(self) -> None:
        """Test PII in lists is handled."""
        event_dict: dict[str, Any] = {"items": ["item1", "item2"]}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["items"] == ["item1", "item2"]

    def test_handles_none_values(self) -> None:
        """Test None values are preserved."""
        event_dict: dict[str, Any] = {"password": None, "data": None}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["password"] is None
        assert result["data"] is None

    def test_redacts_bytes_as_binary_data(self) -> None:
        """Test bytes are marked as binary data."""
        event_dict: dict[str, Any] = {"content": b"binary content"}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["content"] == "[BINARY DATA]"

    def test_redacts_authorization_field(self) -> None:
        """Test authorization fields are redacted."""
        event_dict: dict[str, Any] = {"authorization": "Bearer xyz"}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["authorization"] == "[REDACTED]"

    def test_redacts_credential_field(self) -> None:
        """Test credential fields are redacted."""
        event_dict: dict[str, Any] = {"user_credential": "cred123"}

        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["user_credential"] == "[REDACTED]"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_with_default_settings(self) -> None:
        """Test configuring logging with defaults."""
        configure_logging()

        logger = get_logger("test")
        assert logger is not None

    def test_configure_with_debug_level(self) -> None:
        """Test configuring logging with DEBUG level."""
        configure_logging(log_level="DEBUG")

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_configure_with_console_format(self) -> None:
        """Test configuring logging with console format."""
        configure_logging(log_format="console")

        logger = get_logger("test")
        assert logger is not None

    def test_configure_with_development_mode(self) -> None:
        """Test configuring logging in development mode."""
        configure_logging(development=True)

        logger = get_logger("test")
        assert logger is not None

    def test_configure_with_additional_pii_patterns(self) -> None:
        """Test configuring logging with additional PII patterns."""
        configure_logging(additional_pii_patterns={"custom_secret"})

        event_dict: dict[str, Any] = {"custom_secret": "value123"}
        result = redact_pii(MagicMock(), "info", event_dict)

        assert result["custom_secret"] == "[REDACTED]"

    def test_configure_rejects_invalid_log_level(self) -> None:
        """Test invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log_level"):
            configure_logging(log_level="INVALID")

    def test_configure_with_warning_level(self) -> None:
        """Test configuring logging with WARNING level."""
        configure_logging(log_level="WARNING")

        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_configure_with_error_level(self) -> None:
        """Test configuring logging with ERROR level."""
        configure_logging(log_level="ERROR")

        root = logging.getLogger()
        assert root.level == logging.ERROR


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_with_name(self) -> None:
        """Test getting logger with specific name."""
        logger = get_logger("my.module")
        assert logger is not None

    def test_get_logger_without_name(self) -> None:
        """Test getting logger without name."""
        logger = get_logger()
        assert logger is not None
