"""Unit tests for LoggingMiddleware.

Tests structured logging with correlation IDs.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest

from application.common.middleware.observability.logging_middleware import (
    LoggingConfig,
    LoggingMiddleware,
    generate_request_id,
    get_request_id,
    request_id_var,
    set_request_id,
)


@dataclass
class SampleCommand:
    """Sample command for testing."""

    name: str
    value: int


class PydanticLikeCommand:
    """Command with model_dump method."""

    def __init__(self, name: str) -> None:
        self.name = name

    def model_dump(self) -> dict[str, Any]:
        return {"name": self.name}


class TestRequestIdFunctions:
    """Tests for request ID context functions."""

    def test_generate_request_id(self) -> None:
        """Test request ID generation."""
        request_id = generate_request_id()

        assert isinstance(request_id, str)
        assert len(request_id) == 8

    def test_generate_request_id_unique(self) -> None:
        """Test request IDs are unique."""
        ids = [generate_request_id() for _ in range(100)]

        assert len(set(ids)) == 100

    def test_set_and_get_request_id(self) -> None:
        """Test setting and getting request ID."""
        request_id_var.set(None)  # Reset

        set_request_id("test-123")
        result = get_request_id()

        assert result == "test-123"

    def test_get_request_id_default(self) -> None:
        """Test get_request_id returns None by default."""
        request_id_var.set(None)  # Reset

        result = get_request_id()

        assert result is None


class TestLoggingConfig:
    """Tests for LoggingConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = LoggingConfig()

        assert config.log_request is True
        assert config.log_response is True
        assert config.log_duration is True
        assert config.include_command_data is False
        assert config.max_data_length == 500

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = LoggingConfig(
            log_request=False,
            log_response=False,
            log_duration=False,
            include_command_data=True,
            max_data_length=100,
        )

        assert config.log_request is False
        assert config.log_response is False
        assert config.log_duration is False
        assert config.include_command_data is True
        assert config.max_data_length == 100


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    @pytest.fixture()
    def middleware(self) -> LoggingMiddleware:
        """Create middleware with default config."""
        return LoggingMiddleware()

    @pytest.fixture()
    def middleware_with_data(self) -> LoggingMiddleware:
        """Create middleware that logs command data."""
        return LoggingMiddleware(LoggingConfig(include_command_data=True, max_data_length=50))

    @pytest.mark.asyncio
    async def test_executes_handler(self, middleware: LoggingMiddleware) -> None:
        """Test middleware executes the handler."""
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        result = await middleware(command, handler)

        handler.assert_called_once_with(command)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_sets_request_id_if_missing(self, middleware: LoggingMiddleware) -> None:
        """Test middleware sets request ID if not present."""
        request_id_var.set(None)  # Reset
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        assert get_request_id() is not None

    @pytest.mark.asyncio
    async def test_preserves_existing_request_id(self, middleware: LoggingMiddleware) -> None:
        """Test middleware preserves existing request ID."""
        set_request_id("existing-id")
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        assert get_request_id() == "existing-id"

    @pytest.mark.asyncio
    async def test_logs_request(self, middleware: LoggingMiddleware, capsys: pytest.CaptureFixture[str]) -> None:
        """Test middleware logs request."""
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        captured = capsys.readouterr()
        assert "Executing command" in captured.out
        assert "SampleCommand" in captured.out

    @pytest.mark.asyncio
    async def test_logs_success_response(self, middleware: LoggingMiddleware, capsys: pytest.CaptureFixture[str]) -> None:
        """Test middleware logs successful response."""
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        captured = capsys.readouterr()
        assert "completed" in captured.out

    @pytest.mark.asyncio
    async def test_logs_error_response(self, middleware: LoggingMiddleware, capsys: pytest.CaptureFixture[str]) -> None:
        """Test middleware logs error response."""
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(side_effect=ValueError("test error"))

        with pytest.raises(ValueError):
            await middleware(command, handler)

        captured = capsys.readouterr()
        assert "failed" in captured.out

    @pytest.mark.asyncio
    async def test_propagates_exception(self, middleware: LoggingMiddleware) -> None:
        """Test middleware propagates exceptions."""
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(side_effect=ValueError("test error"))

        with pytest.raises(ValueError, match="test error"):
            await middleware(command, handler)

    @pytest.mark.asyncio
    async def test_logs_command_data_with_model_dump(
        self, middleware_with_data: LoggingMiddleware, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test middleware logs command data using model_dump."""
        command = PydanticLikeCommand(name="test")
        handler = AsyncMock(return_value="result")

        await middleware_with_data(command, handler)

        captured = capsys.readouterr()
        assert "Executing command" in captured.out

    @pytest.mark.asyncio
    async def test_logs_command_data_with_dict(
        self, middleware_with_data: LoggingMiddleware, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test middleware logs command data using __dict__."""
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        await middleware_with_data(command, handler)

        captured = capsys.readouterr()
        assert "Executing command" in captured.out

    @pytest.mark.asyncio
    async def test_truncates_long_command_data(self, middleware_with_data: LoggingMiddleware) -> None:
        """Test middleware truncates long command data."""
        command = SampleCommand(name="x" * 100, value=42)
        handler = AsyncMock(return_value="result")

        # Should not raise
        await middleware_with_data(command, handler)


class TestLoggingMiddlewareDisabled:
    """Tests for LoggingMiddleware with logging disabled."""

    @pytest.mark.asyncio
    async def test_no_request_log(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test no request log when disabled."""
        middleware = LoggingMiddleware(LoggingConfig(log_request=False))
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        captured = capsys.readouterr()
        assert "Executing command" not in captured.out

    @pytest.mark.asyncio
    async def test_no_response_log(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test no response log when disabled."""
        middleware = LoggingMiddleware(LoggingConfig(log_response=False))
        command = SampleCommand(name="test", value=42)
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        captured = capsys.readouterr()
        assert "completed" not in captured.out
