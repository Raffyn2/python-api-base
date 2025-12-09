"""Unit tests for infrastructure/resilience/circuit_breaker.py.

Tests circuit breaker states and transitions.

**Feature: test-coverage-90-percent**
**Validates: Requirements 4.3**
"""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_default_config(self) -> None:
        """Default config should have sensible defaults."""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == timedelta(seconds=30)
        assert config.half_open_max_calls == 3

    def test_custom_config(self) -> None:
        """Custom config should accept custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout=timedelta(seconds=60),
            half_open_max_calls=5
        )
        
        assert config.failure_threshold == 3
        assert config.success_threshold == 1
        assert config.timeout == timedelta(seconds=60)
        assert config.half_open_max_calls == 5


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_states_exist(self) -> None:
        """All expected states should exist."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_init_with_defaults(self) -> None:
        """CircuitBreaker should initialize with defaults."""
        cb = CircuitBreaker("test")
        
        assert cb.name == "test"
        assert cb.state == CircuitState.CLOSED

    def test_init_with_custom_config(self) -> None:
        """CircuitBreaker should accept custom config."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        
        assert cb._config.failure_threshold == 3

    def test_initial_state_is_closed(self) -> None:
        """Initial state should be CLOSED."""
        cb = CircuitBreaker("test")
        
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_call_stays_closed(self) -> None:
        """Successful calls should keep circuit CLOSED."""
        cb = CircuitBreaker("test")
        
        async def success() -> str:
            return "ok"
        
        result = await cb.execute(success)
        
        assert result.is_ok()
        assert result.unwrap() == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failures_open_circuit(self) -> None:
        """Enough failures should open the circuit."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        
        async def fail() -> str:
            raise ValueError("error")
        
        # Cause failures
        for _ in range(3):
            result = await cb.execute(fail)
            assert result.is_err()
        
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self) -> None:
        """Open circuit should reject calls."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config)
        
        async def fail() -> str:
            raise ValueError("error")
        
        # Open the circuit
        await cb.execute(fail)
        assert cb.state == CircuitState.OPEN
        
        # Next call should be rejected
        async def success() -> str:
            return "ok"
        
        result = await cb.execute(success)
        
        assert result.is_err()
        assert "is open" in str(result.error)  # type: ignore

    @pytest.mark.asyncio
    async def test_timeout_transitions_to_half_open(self) -> None:
        """After timeout, circuit should transition to HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=timedelta(seconds=0)  # Immediate timeout
        )
        cb = CircuitBreaker("test", config)
        
        async def fail() -> str:
            raise ValueError("error")
        
        # Open the circuit
        await cb.execute(fail)
        assert cb._state == CircuitState.OPEN
        
        # Check state (should transition due to zero timeout)
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self) -> None:
        """Successful calls in HALF_OPEN should close circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=timedelta(seconds=0)
        )
        cb = CircuitBreaker("test", config)
        
        async def fail() -> str:
            raise ValueError("error")
        
        async def success() -> str:
            return "ok"
        
        # Open the circuit
        await cb.execute(fail)
        
        # Transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
        
        # Successful calls should close it
        await cb.execute(success)
        await cb.execute(success)
        
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_opens_circuit(self) -> None:
        """Failure in HALF_OPEN should open circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=timedelta(seconds=0)
        )
        cb = CircuitBreaker("test", config)
        
        async def fail() -> str:
            raise ValueError("error")
        
        # Open the circuit
        await cb.execute(fail)
        
        # Transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
        
        # Failure should open it again
        await cb.execute(fail)
        
        assert cb._state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_max_calls_limit(self) -> None:
        """HALF_OPEN should limit concurrent calls."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=timedelta(seconds=0),
            half_open_max_calls=2
        )
        cb = CircuitBreaker("test", config)
        
        async def fail() -> str:
            raise ValueError("error")
        
        async def success() -> str:
            return "ok"
        
        # Open the circuit
        await cb.execute(fail)
        
        # Transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
        
        # First two calls should be allowed
        result1 = await cb.execute(success)
        result2 = await cb.execute(success)
        
        assert result1.is_ok()
        assert result2.is_ok()

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self) -> None:
        """Success should reset failure count in CLOSED state."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        
        async def fail() -> str:
            raise ValueError("error")
        
        async def success() -> str:
            return "ok"
        
        # Cause some failures (but not enough to open)
        await cb.execute(fail)
        await cb.execute(fail)
        
        # Success should reset count
        await cb.execute(success)
        
        # Two more failures shouldn't open (count was reset)
        await cb.execute(fail)
        await cb.execute(fail)
        
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_execute_returns_result(self) -> None:
        """execute should return Result type."""
        cb = CircuitBreaker("test")
        
        async def success() -> int:
            return 42
        
        result = await cb.execute(success)
        
        assert result.is_ok()
        assert result.unwrap() == 42

    @pytest.mark.asyncio
    async def test_execute_captures_exception(self) -> None:
        """execute should capture exception in Err."""
        cb = CircuitBreaker("test")
        
        async def fail() -> str:
            raise ValueError("test error")
        
        result = await cb.execute(fail)
        
        assert result.is_err()
        assert isinstance(result.error, ValueError)  # type: ignore
