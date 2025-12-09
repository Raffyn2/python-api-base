"""Unit tests for infrastructure/resilience/retry_pattern.py.

Tests retry logic with backoff.

**Task 20.2: Create tests for retry_pattern.py**
**Requirements: 4.3**
"""

import pytest

from core.base.patterns.result import Err, Ok
from infrastructure.resilience.retry_pattern import (
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

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            base_delay_seconds=0.5,
            max_delay_seconds=30.0,
        )

        assert config.max_attempts == 5
        assert config.base_delay_seconds == 0.5
        assert config.max_delay_seconds == 30.0

    def test_immutability(self) -> None:
        """Test config is immutable."""
        config = RetryConfig()

        with pytest.raises(AttributeError):
            config.max_attempts = 10


class TestExponentialBackoff:
    """Tests for ExponentialBackoff."""

    def test_first_attempt_delay(self) -> None:
        """Test first attempt uses base delay."""
        config = RetryConfig(base_delay_seconds=1.0, jitter=False)
        backoff = ExponentialBackoff(config)

        delay = backoff.get_delay(1)

        assert delay == 1.0

    def test_exponential_increase(self) -> None:
        """Test delay increases exponentially."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        backoff = ExponentialBackoff(config)

        assert backoff.get_delay(1) == 1.0
        assert backoff.get_delay(2) == 2.0
        assert backoff.get_delay(3) == 4.0
        assert backoff.get_delay(4) == 8.0

    def test_max_delay_cap(self) -> None:
        """Test delay is capped at max."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            max_delay_seconds=5.0,
            jitter=False,
        )
        backoff = ExponentialBackoff(config)

        delay = backoff.get_delay(10)

        assert delay == 5.0

    def test_jitter_adds_randomness(self) -> None:
        """Test jitter adds randomness to delay."""
        config = RetryConfig(base_delay_seconds=1.0, jitter=True)
        backoff = ExponentialBackoff(config)

        delays = [backoff.get_delay(1) for _ in range(10)]

        # With jitter, delays should vary
        assert len(set(delays)) > 1


class TestRetry:
    """Tests for Retry class."""

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful execution returns Ok."""
        retry = Retry[str]()

        async def success() -> str:
            return "result"

        result = await retry.execute(success)

        assert isinstance(result, Ok)
        assert result.unwrap() == "result"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self) -> None:
        """Test retry on transient failure."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)
        attempts = 0

        async def fail_then_succeed() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Transient error")
            return "success"

        result = await retry.execute(fail_then_succeed)

        assert isinstance(result, Ok)
        assert result.unwrap() == "success"
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_all_retries_fail(self) -> None:
        """Test all retries failing returns Err."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)

        async def always_fail() -> str:
            raise ValueError("Always fails")

        result = await retry.execute(always_fail)

        assert isinstance(result, Err)
        # Access the error value directly from the Err object
        assert "Always fails" in str(result.error)

    @pytest.mark.asyncio
    async def test_retries_on_matching_exception(self) -> None:
        """Test retry on matching exception types."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        retry = Retry[str](config)
        attempts = 0

        async def fail_with_value_error() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Retryable")
            return "success"

        result = await retry.execute(
            fail_with_value_error,
            retryable_exceptions=(ValueError,),
        )

        assert isinstance(result, Ok)
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_max_attempts_respected(self) -> None:
        """Test max attempts is respected."""
        config = RetryConfig(max_attempts=5, base_delay_seconds=0.01)
        retry = Retry[str](config)
        attempts = 0

        async def always_fail() -> str:
            nonlocal attempts
            attempts += 1
            raise ValueError("Fail")

        await retry.execute(always_fail)

        assert attempts == 5

    @pytest.mark.asyncio
    async def test_custom_backoff(self) -> None:
        """Test using custom backoff strategy."""

        class ConstantBackoff:
            def get_delay(self, attempt: int) -> float:
                return 0.01

        config = RetryConfig(max_attempts=3)
        retry = Retry[str](config, backoff=ConstantBackoff())
        attempts = 0

        async def fail_twice() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Fail")
            return "success"

        result = await retry.execute(fail_twice)

        assert isinstance(result, Ok)
        assert attempts == 3
