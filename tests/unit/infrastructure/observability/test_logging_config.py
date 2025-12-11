"""Tests for logging configuration module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.3**
"""

import json
import logging

from infrastructure.observability.logging_config import JSONFormatter, configure_logging


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_basic_message(self) -> None:
        """Test formatting a basic log message."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_format_with_correlation_id(self) -> None:
        """Test formatting with correlation ID."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.correlation_id = "abc-123"
        result = formatter.format(record)
        data = json.loads(result)

        assert data["correlation_id"] == "abc-123"

    def test_format_with_exception(self) -> None:
        """Test formatting with exception info."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "Test error" in data["exception"]

    def test_format_with_extra_data(self) -> None:
        """Test formatting with extra data."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra = {"user_id": "123", "action": "login"}
        result = formatter.format(record)
        data = json.loads(result)

        assert data["user_id"] == "123"
        assert data["action"] == "login"

    def test_format_different_levels(self) -> None:
        """Test formatting different log levels."""
        formatter = JSONFormatter()
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level, level_name in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )
            result = formatter.format(record)
            data = json.loads(result)
            assert data["level"] == level_name

    def test_format_with_message_args(self) -> None:
        """Test formatting with message arguments."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User %s logged in from %s",
            args=("john", "192.168.1.1"),
            exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)

        assert data["message"] == "User john logged in from 192.168.1.1"

    def test_format_includes_module_and_function(self) -> None:
        """Test that format includes module and function."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"
        result = formatter.format(record)
        data = json.loads(result)

        assert data["module"] == "test_module"
        assert data["function"] == "test_function"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_with_json_format(self) -> None:
        """Test configuring with JSON format."""
        configure_logging(level="INFO", json_format=True)
        root = logging.getLogger()
        assert root.level == logging.INFO
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, JSONFormatter)

    def test_configure_with_text_format(self) -> None:
        """Test configuring with text format."""
        configure_logging(level="DEBUG", json_format=False)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1
        assert not isinstance(root.handlers[0].formatter, JSONFormatter)

    def test_configure_different_levels(self) -> None:
        """Test configuring different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            configure_logging(level=level)
            root = logging.getLogger()
            assert root.level == getattr(logging, level)

    def test_configure_lowercase_level(self) -> None:
        """Test configuring with lowercase level."""
        configure_logging(level="debug")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_configure_replaces_handlers(self) -> None:
        """Test that configure replaces existing handlers."""
        root = logging.getLogger()
        # Add extra handler
        root.addHandler(logging.StreamHandler())
        len(root.handlers)

        configure_logging()

        # Should have exactly one handler after configure
        assert len(root.handlers) == 1
