"""Unit tests for RetryMiddleware.

Tests retry logic with exponential backoff.
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from application.common.middleware.resilience.retry import (
    RetryConfig,
    RetryExhaustedError,
    RetryMiddleware,
)


@dataclass
class SampleCommand:
    """Sample command for testing."""

    name: str


class TestRetryExhaustedError:
    """Tests for RetryExhaustedError."""

    def test_error_attributes(self) -> None:
        """Test error attributes."""
        last_error = ValueError("original error")
        error = RetryExhaustedError(
            message="test message",
            attempts=3,
            last_error=last_error,
        )

        assert "test message" in str(error)
        assert error.attempts == 3
        assert error.last_error is last_error


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert TimeoutError in config.retryable_exceptions

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=60.0,
            exponential_base=3.0,
            jitter=False,
            retryable_exceptions=(ValueError,),
        )

        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 60.0
        assert config.exponential_base == 3.0
        assert config.jitter is False


class TestRetryMiddleware:
    """Tests for RetryMiddleware."""

    @pytest.fixture()
    def middleware(self) -> RetryMiddleware:
        """Create middleware with fast config for testing."""
        config = RetryConfig(
            max_retries=2,
            base_delay=0.01,
            max_delay=0.1,
            jitter=False,
            retryable_exceptions=(ValueError,),
        )
        return RetryMiddleware(config)

    @pytest.mark.asyncio
    async def test_success_no_retry(self, middleware: RetryMiddleware) -> None:
        """Test successful call without retry."""
        command = SampleCommand(name="test")
        handler = AsyncMock(return_value="result")

        result = await middleware(command, handler)

        assert result == "result"
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, middleware: RetryMiddleware) -> None:
        """Test retry on retryable failure."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=[ValueError("error"), "result"])

        result = await middleware(command, handler)

        assert result == "result"
        assert handler.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, middleware: RetryMiddleware) -> None:
        """Test retry exhaustion."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=ValueError("error"))

        with pytest.raises(RetryExhaustedError) as exc_info:
            await middleware(command, handler)

        assert exc_info.value.attempts == 3  # max_retries + 1
        assert handler.call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_exception(self, middleware: RetryMiddleware) -> None:
        """Test non-retryable exception is not retried."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=TypeError("not retryable"))

        with pytest.raises(TypeError):
            await middleware(command, handler)

        handler.assert_called_once()

    def test_calculate_delay_exponential(self) -> None:
        """Test exponential delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=False,
        )
        middleware = RetryMiddleware(config)

        assert middleware._calculate_delay(0) == 1.0
        assert middleware._calculate_delay(1) == 2.0
        assert middleware._calculate_delay(2) == 4.0

    def test_calculate_delay_max_cap(self) -> None:
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=10.0,
            exponential_base=2.0,
            max_delay=15.0,
            jitter=False,
        )
        middleware = RetryMiddleware(config)

        assert middleware._calculate_delay(2) == 15.0  # Would be 40 without cap

    def test_calculate_delay_with_jitter(self) -> None:
        """Test delay with jitter varies."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=True,
        )
        middleware = RetryMiddleware(config)

        delays = [middleware._calculate_delay(0) for _ in range(10)]

        # With jitter, delays should vary
        assert len(set(delays)) > 1

    def test_is_retryable_true(self, middleware: RetryMiddleware) -> None:
        """Test is_retryable returns True for configured exceptions."""
        assert middleware._is_retryable(ValueError("error")) is True

    def test_is_retryable_false(self, middleware: RetryMiddleware) -> None:
        """Test is_retryable returns False for non-configured exceptions."""
        assert middleware._is_retryable(TypeError("error")) is False

    def test_default_config(self) -> None:
        """Test middleware with default config."""
        middleware = RetryMiddleware()

        assert middleware._config.max_retries == 3

    @pytest.mark.asyncio
    async def test_success_after_multiple_retries(self, middleware: RetryMiddleware) -> None:
        """Test success after multiple retries."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=[ValueError("1"), ValueError("2"), "result"])

        result = await middleware(command, handler)

        assert result == "result"
        assert handler.call_count == 3
