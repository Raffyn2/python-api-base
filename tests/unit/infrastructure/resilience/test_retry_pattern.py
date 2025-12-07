"""Tests for retry pattern implementation.

**Feature: realistic-test-coverage**
**Validates: Requirements 16.2**
"""

import pytest

from core.base.patterns.result import Err, Ok
from infrastructure.resilience.retry_pattern import (
    BackoffStrategy,
    ExponentialBackoff,
    Retry,
    RetryConfig,
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_max_attempts(self) -> None:
        """Test custom max attempts."""
        config = RetryConfig(max_attempts=5)
        assert config.max_attempts == 5

    def test_custom_base_delay(self) -> None:
        """Test custom base delay."""
        config = RetryConfig(base_delay_seconds=0.5)
        assert config.base_delay_seconds == 0.5

    def test_custom_max_delay(self) -> None:
        """Test custom max delay."""
        config = RetryConfig(max_delay_seconds=120.0)
        assert config.max_delay_seconds == 120.0

    def test_custom_exponential_base(self) -> None:
        """Test custom exponential base."""
        config = RetryConfig(exponential_base=3.0)
        assert config.exponential_base == 3.0

    def test_disable_jitter(self) -> None:
        """Test disabling jitter."""
        config = RetryConfig(jitter=False)
        assert config.jitter is False

    def test_frozen_dataclass(self) -> None:
        """Test that config is immutable."""
        config = RetryConfig()
        with pytest.raises(AttributeError):
            config.max_attempts = 10


class TestExponentialBackoff:
    """Tests for ExponentialBackoff."""

    def test_first_attempt_delay(self) -> None:
        """Test delay for first attempt."""
        config = RetryConfig(base_delay_seconds=1.0, jitter=False)
        backoff = ExponentialBackoff(config)
        delay = backoff.get_delay(1)
        assert delay == 1.0

    def test_second_attempt_delay(self) -> None:
        """Test delay for second attempt."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        backoff = ExponentialBackoff(config)
        delay = backoff.get_delay(2)
        assert delay == 2.0

    def test_third_attempt_delay(self) -> None:
        """Test delay for third attempt."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        backoff = ExponentialBackoff(config)
        delay = backoff.get_delay(3)
        assert delay == 4.0

    def test_respects_max_delay(self) -> None:
        """Test that delay respects max delay."""
        config = RetryConfig(
            base_delay_seconds=10.0,
            max_delay_seconds=30.0,
            exponential_base=2.0,
            jitter=False,
        )
        backoff = ExponentialBackoff(config)
        delay = backoff.get_delay(5)  # Would be 160s without cap
        assert delay == 30.0

    def test_jitter_adds_randomness(self) -> None:
        """Test that jitter adds randomness."""
        config = RetryConfig(base_delay_seconds=1.0, jitter=True)
        backoff = ExponentialBackoff(config)

        # Get multiple delays and check they vary
        delays = [backoff.get_delay(1) for _ in range(10)]
        # With jitter, delays should vary between 0.5 and 1.5
        assert all(0.5 <= d <= 1.5 for d in delays)
        # At least some should be different
        assert len(set(delays)) > 1

    def test_implements_backoff_strategy(self) -> None:
        """Test that ExponentialBackoff implements BackoffStrategy."""
        config = RetryConfig()
        backoff = ExponentialBackoff(config)
        assert isinstance(backoff, BackoffStrategy)


class TestRetry:
    """Tests for Retry class."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        """Test successful execution on first attempt."""
        retry = Retry[str]()

        async def operation() -> str:
            return "success"

        result = await retry.execute(operation)

        assert isinstance(result, Ok)
        assert result.value == "success"

    @pytest.mark.asyncio
    async def test_success_after_retry(self) -> None:
        """Test successful execution after retry."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        attempts = 0

        async def operation() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Temporary error")
            return "success"

        result = await retry.execute(operation)

        assert isinstance(result, Ok)
        assert result.value == "success"
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_all_retries_fail(self) -> None:
        """Test when all retries fail."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        async def operation() -> str:
            raise ValueError("Always fails")

        result = await retry.execute(operation)

        assert isinstance(result, Err)
        assert isinstance(result.error, ValueError)

    @pytest.mark.asyncio
    async def test_retryable_exceptions_filter(self) -> None:
        """Test that only retryable exceptions trigger retry."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        attempts = 0

        async def operation() -> str:
            nonlocal attempts
            attempts += 1
            raise TypeError("Non-retryable")

        # Non-retryable exceptions are propagated, not caught
        with pytest.raises(TypeError):
            await retry.execute(
                operation,
                retryable_exceptions=(ValueError,),  # TypeError not included
            )

        assert attempts == 1  # No retry for TypeError

    @pytest.mark.asyncio
    async def test_custom_backoff_strategy(self) -> None:
        """Test with custom backoff strategy."""

        class ConstantBackoff:
            def get_delay(self, attempt: int) -> float:
                return 0.01

        config = RetryConfig(max_attempts=3)
        retry = Retry[str](config, backoff=ConstantBackoff())

        attempts = 0

        async def operation() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Retry")
            return "success"

        result = await retry.execute(operation)

        assert isinstance(result, Ok)
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_default_config(self) -> None:
        """Test with default configuration."""
        retry = Retry[int]()

        async def operation() -> int:
            return 42

        result = await retry.execute(operation)

        assert isinstance(result, Ok)
        assert result.value == 42

    @pytest.mark.asyncio
    async def test_max_attempts_respected(self) -> None:
        """Test that max attempts is respected."""
        config = RetryConfig(max_attempts=2, base_delay_seconds=0.01)
        retry = Retry[str](config)

        attempts = 0

        async def operation() -> str:
            nonlocal attempts
            attempts += 1
            raise ValueError("Always fails")

        await retry.execute(operation)

        assert attempts == 2

    @pytest.mark.asyncio
    async def test_returns_last_error(self) -> None:
        """Test that last error is returned."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        attempt_count = 0

        async def operation() -> str:
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError(f"Error {attempt_count}")

        result = await retry.execute(operation)

        assert isinstance(result, Err)
        assert "Error 3" in str(result.error)
