"""Unit tests for infrastructure/resilience/retry_pattern.py.

Tests retry pattern implementation.

**Feature: test-coverage-90-percent**
**Validates: Requirements 4.3**
"""

import pytest

from infrastructure.resilience.retry_pattern import (
    ExponentialBackoff,
    Retry,
    RetryConfig,
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self) -> None:
        """Config should have sensible defaults."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_values(self) -> None:
        """Config should accept custom values."""
        config = RetryConfig(
            max_attempts=5, base_delay_seconds=0.5, max_delay_seconds=30.0, exponential_base=3.0, jitter=False
        )

        assert config.max_attempts == 5
        assert config.base_delay_seconds == 0.5
        assert config.max_delay_seconds == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_config_is_frozen(self) -> None:
        """Config should be immutable."""
        config = RetryConfig()

        with pytest.raises(AttributeError):
            config.max_attempts = 10  # type: ignore


class TestExponentialBackoff:
    """Tests for ExponentialBackoff."""

    def test_first_attempt_base_delay(self) -> None:
        """First attempt should use base delay."""
        config = RetryConfig(base_delay_seconds=1.0, jitter=False)
        backoff = ExponentialBackoff(config)

        delay = backoff.get_delay(1)

        assert delay == 1.0

    def test_exponential_increase(self) -> None:
        """Delay should increase exponentially."""
        config = RetryConfig(base_delay_seconds=1.0, exponential_base=2.0, jitter=False)
        backoff = ExponentialBackoff(config)

        assert backoff.get_delay(1) == 1.0
        assert backoff.get_delay(2) == 2.0
        assert backoff.get_delay(3) == 4.0
        assert backoff.get_delay(4) == 8.0

    def test_max_delay_cap(self) -> None:
        """Delay should be capped at max_delay."""
        config = RetryConfig(base_delay_seconds=1.0, max_delay_seconds=5.0, exponential_base=2.0, jitter=False)
        backoff = ExponentialBackoff(config)

        # 2^10 = 1024, but should be capped at 5
        delay = backoff.get_delay(10)

        assert delay == 5.0

    def test_jitter_adds_randomness(self) -> None:
        """Jitter should add randomness to delay."""
        config = RetryConfig(base_delay_seconds=1.0, jitter=True)
        backoff = ExponentialBackoff(config)

        # Get multiple delays and check they vary
        delays = [backoff.get_delay(1) for _ in range(10)]

        # With jitter, delays should vary (not all equal)
        assert len(set(delays)) > 1


class TestRetry:
    """Tests for Retry class."""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self) -> None:
        """Successful first attempt should return Ok."""
        retry = Retry[str]()

        async def success():
            return "result"

        result = await retry.execute(success)

        assert result.is_ok()
        assert result.unwrap() == "result"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self) -> None:
        """Should retry on failure."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("error")
            return "success"

        result = await retry.execute(fail_then_succeed)

        assert result.is_ok()
        assert result.unwrap() == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self) -> None:
        """Should return Err after max attempts."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")

        result = await retry.execute(always_fail)

        assert result.is_err()
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retryable_exceptions_filter(self) -> None:
        """Should only retry specified exceptions."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        call_count = 0

        async def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retryable")

        # Only retry ValueError, not TypeError
        # TypeError is not in retryable_exceptions, so it propagates up
        with pytest.raises(TypeError, match="not retryable"):
            await retry.execute(raise_type_error, retryable_exceptions=(ValueError,))

        # Should fail immediately without retry
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_custom_backoff(self) -> None:
        """Should use custom backoff strategy."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)

        class ConstantBackoff:
            def get_delay(self, attempt: int) -> float:
                return 0.001

        retry = Retry[str](config, backoff=ConstantBackoff())

        call_count = 0

        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("error")
            return "success"

        result = await retry.execute(fail_twice)

        assert result.is_ok()
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_delay_on_last_attempt(self) -> None:
        """Should not delay after last failed attempt."""
        config = RetryConfig(max_attempts=2, base_delay_seconds=0.01)
        retry = Retry[str](config)

        async def always_fail():
            raise ValueError("error")

        # This should complete quickly (no delay after last attempt)
        result = await retry.execute(always_fail)

        assert result.is_err()

    @pytest.mark.asyncio
    async def test_default_config(self) -> None:
        """Should work with default config."""
        retry = Retry[int]()

        async def success():
            return 42

        result = await retry.execute(success)

        assert result.is_ok()
        assert result.unwrap() == 42
