"""Unit tests for CircuitBreakerMiddleware.

Tests circuit breaker states and transitions.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from application.common.middleware.resilience.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CircuitBreakerOpenError,
    CircuitBreakerStats,
    CircuitState,
)


@dataclass
class SampleCommand:
    """Sample command for testing."""

    name: str


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_closed_value(self) -> None:
        """Test CLOSED value."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_value(self) -> None:
        """Test OPEN value."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_value(self) -> None:
        """Test HALF_OPEN value."""
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerOpenError:
    """Tests for CircuitBreakerOpenError."""

    def test_error_message(self) -> None:
        """Test error message."""
        recovery = datetime.now(UTC)
        error = CircuitBreakerOpenError("test message", recovery)

        assert "test message" in str(error)
        assert error.recovery_time == recovery


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.half_open_max_calls == 1
        assert config.monitored_exceptions == (Exception,)

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            half_open_max_calls=2,
            monitored_exceptions=(ValueError, TypeError),
        )

        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30.0
        assert config.half_open_max_calls == 2


class TestCircuitBreakerStats:
    """Tests for CircuitBreakerStats."""

    def test_default_values(self) -> None:
        """Test default stats values."""
        stats = CircuitBreakerStats()

        assert stats.state == CircuitState.CLOSED
        assert stats.failure_count == 0
        assert stats.success_count == 0
        assert stats.last_failure_time is None
        assert stats.half_open_calls == 0


class TestCircuitBreakerMiddleware:
    """Tests for CircuitBreakerMiddleware."""

    @pytest.fixture
    def middleware(self) -> CircuitBreakerMiddleware:
        """Create middleware with low threshold for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1.0,
            half_open_max_calls=1,
        )
        return CircuitBreakerMiddleware(config)

    @pytest.mark.asyncio
    async def test_closed_state_success(
        self, middleware: CircuitBreakerMiddleware
    ) -> None:
        """Test successful call in closed state."""
        command = SampleCommand(name="test")
        handler = AsyncMock(return_value="result")

        result = await middleware(command, handler)

        assert result == "result"
        assert middleware.state == CircuitState.CLOSED
        assert middleware.stats.success_count == 1

    @pytest.mark.asyncio
    async def test_closed_state_failure(
        self, middleware: CircuitBreakerMiddleware
    ) -> None:
        """Test failed call in closed state."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=ValueError("error"))

        with pytest.raises(ValueError):
            await middleware(command, handler)

        assert middleware.stats.failure_count == 1

    @pytest.mark.asyncio
    async def test_opens_after_threshold(
        self, middleware: CircuitBreakerMiddleware
    ) -> None:
        """Test circuit opens after failure threshold."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=ValueError("error"))

        # Trigger failures up to threshold
        for _ in range(2):
            with pytest.raises(ValueError):
                await middleware(command, handler)

        assert middleware.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_state_rejects(
        self, middleware: CircuitBreakerMiddleware
    ) -> None:
        """Test open circuit rejects calls."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=ValueError("error"))

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await middleware(command, handler)

        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            await middleware(command, handler)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(
        self, middleware: CircuitBreakerMiddleware
    ) -> None:
        """Test circuit enters half-open after timeout."""
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=ValueError("error"))

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await middleware(command, handler)

        # Simulate timeout passed
        middleware._stats.last_failure_time = datetime.now(UTC) - timedelta(seconds=2)

        # Reset handler to succeed
        handler.side_effect = None
        handler.return_value = "result"

        result = await middleware(command, handler)

        assert result == "result"
        assert middleware.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_success_closes(
        self, middleware: CircuitBreakerMiddleware
    ) -> None:
        """Test successful call in half-open closes circuit."""
        middleware._stats.state = CircuitState.HALF_OPEN
        command = SampleCommand(name="test")
        handler = AsyncMock(return_value="result")

        result = await middleware(command, handler)

        assert result == "result"
        assert middleware.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_limit(
        self, middleware: CircuitBreakerMiddleware
    ) -> None:
        """Test half-open call limit."""
        middleware._stats.state = CircuitState.HALF_OPEN
        middleware._stats.half_open_calls = 1  # Already at limit
        command = SampleCommand(name="test")
        handler = AsyncMock(return_value="result")

        with pytest.raises(CircuitBreakerOpenError):
            await middleware(command, handler)

    @pytest.mark.asyncio
    async def test_unmonitored_exception_not_counted(self) -> None:
        """Test unmonitored exceptions don't trip circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            monitored_exceptions=(ValueError,),
        )
        middleware = CircuitBreakerMiddleware(config)
        command = SampleCommand(name="test")
        handler = AsyncMock(side_effect=TypeError("not monitored"))

        with pytest.raises(TypeError):
            await middleware(command, handler)

        assert middleware.stats.failure_count == 0

    def test_state_property(self, middleware: CircuitBreakerMiddleware) -> None:
        """Test state property."""
        assert middleware.state == CircuitState.CLOSED

    def test_stats_property(self, middleware: CircuitBreakerMiddleware) -> None:
        """Test stats property."""
        stats = middleware.stats

        assert isinstance(stats, CircuitBreakerStats)

    def test_default_config(self) -> None:
        """Test middleware with default config."""
        middleware = CircuitBreakerMiddleware()

        assert middleware._config.failure_threshold == 5
