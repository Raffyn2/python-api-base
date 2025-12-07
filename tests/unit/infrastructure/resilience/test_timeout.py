"""Tests for timeout pattern implementation.

**Feature: realistic-test-coverage**
**Validates: Requirements 16.3**
"""

import asyncio

import pytest

from core.base.patterns.result import Err, Ok
from infrastructure.resilience.timeout import Timeout, TimeoutConfig


class TestTimeoutConfig:
    """Tests for TimeoutConfig."""

    def test_create_with_duration(self) -> None:
        """Test creating config with duration."""
        config = TimeoutConfig(duration_seconds=5.0)
        assert config.duration_seconds == 5.0
        assert config.message == "Operation timed out"

    def test_create_with_custom_message(self) -> None:
        """Test creating config with custom message."""
        config = TimeoutConfig(
            duration_seconds=10.0,
            message="Custom timeout message",
        )
        assert config.message == "Custom timeout message"

    def test_frozen_dataclass(self) -> None:
        """Test that config is immutable."""
        config = TimeoutConfig(duration_seconds=5.0)
        with pytest.raises(AttributeError):
            config.duration_seconds = 10.0

    def test_zero_duration(self) -> None:
        """Test config with zero duration."""
        config = TimeoutConfig(duration_seconds=0.0)
        assert config.duration_seconds == 0.0

    def test_fractional_duration(self) -> None:
        """Test config with fractional duration."""
        config = TimeoutConfig(duration_seconds=0.5)
        assert config.duration_seconds == 0.5


class TestTimeout:
    """Tests for Timeout class."""

    @pytest.mark.asyncio
    async def test_execute_completes_before_timeout(self) -> None:
        """Test execution that completes before timeout."""
        config = TimeoutConfig(duration_seconds=1.0)
        timeout = Timeout[str](config)

        async def fast_operation() -> str:
            return "success"

        result = await timeout.execute(fast_operation)

        assert isinstance(result, Ok)
        assert result.value == "success"

    @pytest.mark.asyncio
    async def test_execute_times_out(self) -> None:
        """Test execution that times out."""
        config = TimeoutConfig(duration_seconds=0.1)
        timeout = Timeout[str](config)

        async def slow_operation() -> str:
            await asyncio.sleep(1.0)
            return "never reached"

        result = await timeout.execute(slow_operation)

        assert isinstance(result, Err)
        assert isinstance(result.error, TimeoutError)

    @pytest.mark.asyncio
    async def test_timeout_error_message(self) -> None:
        """Test that timeout error has correct message."""
        config = TimeoutConfig(
            duration_seconds=0.1,
            message="Custom timeout",
        )
        timeout = Timeout[str](config)

        async def slow_operation() -> str:
            await asyncio.sleep(1.0)
            return "never reached"

        result = await timeout.execute(slow_operation)

        assert isinstance(result, Err)
        assert str(result.error) == "Custom timeout"

    @pytest.mark.asyncio
    async def test_execute_with_return_value(self) -> None:
        """Test execution returns correct value."""
        config = TimeoutConfig(duration_seconds=1.0)
        timeout = Timeout[int](config)

        async def compute() -> int:
            return 42

        result = await timeout.execute(compute)

        assert isinstance(result, Ok)
        assert result.value == 42

    @pytest.mark.asyncio
    async def test_execute_with_complex_return_type(self) -> None:
        """Test execution with complex return type."""
        config = TimeoutConfig(duration_seconds=1.0)
        timeout = Timeout[dict[str, int]](config)

        async def get_data() -> dict[str, int]:
            return {"a": 1, "b": 2}

        result = await timeout.execute(get_data)

        assert isinstance(result, Ok)
        assert result.value == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_execute_with_none_return(self) -> None:
        """Test execution with None return."""
        config = TimeoutConfig(duration_seconds=1.0)
        timeout = Timeout[None](config)

        async def void_operation() -> None:
            pass

        result = await timeout.execute(void_operation)

        assert isinstance(result, Ok)
        assert result.value is None

    @pytest.mark.asyncio
    async def test_execute_just_before_timeout(self) -> None:
        """Test execution that completes just before timeout."""
        config = TimeoutConfig(duration_seconds=0.5)
        timeout = Timeout[str](config)

        async def operation() -> str:
            await asyncio.sleep(0.1)
            return "completed"

        result = await timeout.execute(operation)

        assert isinstance(result, Ok)
        assert result.value == "completed"

    @pytest.mark.asyncio
    async def test_multiple_executions(self) -> None:
        """Test multiple executions with same timeout instance."""
        config = TimeoutConfig(duration_seconds=1.0)
        timeout = Timeout[int](config)

        async def operation(n: int) -> int:
            return n * 2

        # Execute multiple times
        result1 = await timeout.execute(lambda: operation(1))
        result2 = await timeout.execute(lambda: operation(2))
        result3 = await timeout.execute(lambda: operation(3))

        assert isinstance(result1, Ok) and result1.value == 2
        assert isinstance(result2, Ok) and result2.value == 4
        assert isinstance(result3, Ok) and result3.value == 6
