"""Tests for circuit breaker pattern implementation.

**Feature: realistic-test-coverage**
**Validates: Requirements 1.3**
"""

from datetime import timedelta
from unittest.mock import patch

import pytest

from core.base.patterns.result import Err, Ok
from infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_closed_value(self) -> None:
        """Test CLOSED state value."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_value(self) -> None:
        """Test OPEN state value."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_value(self) -> None:
        """Test HALF_OPEN state value."""
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == timedelta(seconds=30)
        assert config.half_open_max_calls == 3

    def test_custom_failure_threshold(self) -> None:
        """Test custom failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=10)
        assert config.failure_threshold == 10

    def test_custom_success_threshold(self) -> None:
        """Test custom success threshold."""
        config = CircuitBreakerConfig(success_threshold=5)
        assert config.success_threshold == 5

    def test_custom_timeout(self) -> None:
        """Test custom timeout."""
        config = CircuitBreakerConfig(timeout=timedelta(seconds=60))
        assert config.timeout == timedelta(seconds=60)

    def test_custom_half_open_max_calls(self) -> None:
        """Test custom half open max calls."""
        config = CircuitBreakerConfig(half_open_max_calls=5)
        assert config.half_open_max_calls == 5


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_initial_state_is_closed(self) -> None:
        """Test that initial state is CLOSED."""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    def test_name_property(self) -> None:
        """Test circuit breaker name."""
        cb = CircuitBreaker("my-circuit")
        assert cb.name == "my-circuit"

    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Test successful execution returns Ok."""
        cb = CircuitBreaker("test")

        async def operation() -> str:
            return "success"

        result = await cb.execute(operation)

        assert isinstance(result, Ok)
        assert result.value == "success"

    @pytest.mark.asyncio
    async def test_failed_execution(self) -> None:
        """Test failed execution returns Err."""
        cb = CircuitBreaker("test")

        async def operation() -> str:
            raise ValueError("error")

        result = await cb.execute(operation)

        assert isinstance(result, Err)
        assert isinstance(result.error, ValueError)

    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(self) -> None:
        """Test circuit opens after reaching failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)

        async def failing_operation() -> str:
            raise ValueError("error")

        # Execute until threshold
        for _ in range(3):
            await cb.execute(failing_operation)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_rejects_when_open(self) -> None:
        """Test circuit rejects calls when open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config)

        async def failing_operation() -> str:
            raise ValueError("error")

        # Open the circuit
        await cb.execute(failing_operation)
        assert cb.state == CircuitState.OPEN

        # Try to execute - should be rejected
        async def success_operation() -> str:
            return "success"

        result = await cb.execute(success_operation)

        assert isinstance(result, Err)
        assert "open" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self) -> None:
        """Test that success resets failure count."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)

        async def failing_operation() -> str:
            raise ValueError("error")

        async def success_operation() -> str:
            return "success"

        # Record some failures
        await cb.execute(failing_operation)
        await cb.execute(failing_operation)

        # Success should reset
        await cb.execute(success_operation)

        # More failures should not open circuit yet
        await cb.execute(failing_operation)
        await cb.execute(failing_operation)

        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self) -> None:
        """Test circuit transitions to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=timedelta(seconds=1),
        )
        cb = CircuitBreaker("test", config)

        async def failing_operation() -> str:
            raise ValueError("error")

        # Open the circuit
        await cb.execute(failing_operation)
        assert cb.state == CircuitState.OPEN

        # Mock time to simulate timeout
        from datetime import datetime, UTC

        future_time = datetime.now(UTC) + timedelta(seconds=2)
        with patch("infrastructure.resilience.circuit_breaker.datetime") as mock_dt:
            mock_dt.now.return_value = future_time
            mock_dt.UTC = UTC
            assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_success_in_half_open(self) -> None:
        """Test circuit closes after successes in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=timedelta(seconds=0),  # Immediate transition
        )
        cb = CircuitBreaker("test", config)

        async def failing_operation() -> str:
            raise ValueError("error")

        async def success_operation() -> str:
            return "success"

        # Open the circuit
        await cb.execute(failing_operation)

        # Force transition to half-open
        cb._state = CircuitState.HALF_OPEN
        cb._success_count = 0

        # Record successes
        await cb.execute(success_operation)
        await cb.execute(success_operation)

        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self) -> None:
        """Test circuit reopens on failure in HALF_OPEN."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config)

        async def failing_operation() -> str:
            raise ValueError("error")

        # Force to half-open state
        cb._state = CircuitState.HALF_OPEN

        # Failure should reopen
        await cb.execute(failing_operation)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_max_calls_limit(self) -> None:
        """Test half open max calls limit."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            half_open_max_calls=2,
        )
        cb = CircuitBreaker("test", config)

        # Force to half-open state
        cb._state = CircuitState.HALF_OPEN
        cb._half_open_calls = 0

        async def success_operation() -> str:
            return "success"

        # First two calls should succeed
        result1 = await cb.execute(success_operation)
        result2 = await cb.execute(success_operation)

        assert isinstance(result1, Ok)
        assert isinstance(result2, Ok)

    def test_can_execute_when_closed(self) -> None:
        """Test _can_execute returns True when closed."""
        cb = CircuitBreaker("test")
        assert cb._can_execute() is True

    def test_can_execute_when_open(self) -> None:
        """Test _can_execute returns False when open."""
        cb = CircuitBreaker("test")
        cb._state = CircuitState.OPEN
        cb._last_failure_time = None
        assert cb._can_execute() is False

    def test_custom_config(self) -> None:
        """Test circuit breaker with custom config."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout=timedelta(minutes=1),
        )
        cb = CircuitBreaker("test", config)
        assert cb._config.failure_threshold == 10
        assert cb._config.success_threshold == 5
