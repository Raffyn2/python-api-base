"""Circuit breaker middleware for fault tolerance.

**Feature: enterprise-features-2025**
**Validates: Requirement 11.2 - Circuit breaker to prevent cascade failures**

Note: This is the CQRS/Application layer circuit breaker for CommandBus.
For HTTP/Infrastructure layer, see: src/infrastructure/resilience/circuit_breaker.py
Architecture decision documented in: docs/architecture/adr/ADR-003-resilience-layers.md
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import structlog

from application.common.errors import ApplicationError

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(ApplicationError):
    """Raised when circuit breaker is open.

    Inherits from ApplicationError for consistent error handling.

    Attributes:
        recovery_time: Estimated time when circuit may recover.
        circuit_name: Name of the circuit breaker (for identification).
    """

    def __init__(
        self,
        message: str,
        recovery_time: datetime,
        circuit_name: str = "default",
    ) -> None:
        self.recovery_time = recovery_time
        self.circuit_name = circuit_name
        super().__init__(
            message=message,
            code="CIRCUIT_BREAKER_OPEN",
            details={
                "recovery_time": recovery_time.isoformat(),
                "circuit_name": circuit_name,
            },
        )


@dataclass(slots=True)
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    success_threshold: int = 1  # Successes needed in HALF_OPEN to close
    recovery_timeout: float = 60.0  # seconds
    half_open_max_calls: int = 1
    monitored_exceptions: tuple[type[Exception], ...] = (Exception,)


@dataclass(slots=True)
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    half_open_calls: int = 0


class CircuitBreakerMiddleware:
    """Middleware that implements circuit breaker pattern.

    Prevents cascade failures by failing fast when a service
    is experiencing issues. States:

    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing fast, requests rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

    Example:
        >>> cb = CircuitBreakerMiddleware(
        ...     name="payment-service",
        ...     config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60),
        ... )
        >>> bus.add_middleware(cb)
    """

    def __init__(
        self,
        config: CircuitBreakerConfig | None = None,
        *,
        name: str = "default",
    ) -> None:
        """Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration.
            name: Circuit breaker name for identification in logs/metrics.
        """
        self._config = config or CircuitBreakerConfig()
        self._stats = CircuitBreakerStats()
        self._name = name

    @property
    def name(self) -> str:
        """Get circuit breaker name."""
        return self._name

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._stats.state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset.

        Returns:
            True if recovery timeout has passed.
        """
        if self._stats.last_failure_time is None:
            return False

        elapsed = (datetime.now(UTC) - self._stats.last_failure_time).total_seconds()
        return elapsed >= self._config.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        self._stats.success_count += 1

        if self._stats.state == CircuitState.HALF_OPEN:
            if self._stats.success_count >= self._config.success_threshold:
                logger.info(
                    "Circuit breaker recovered, closing",
                    circuit_name=self._name,
                    success_count=self._stats.success_count,
                    operation="CIRCUIT_CLOSED",
                )
                self._stats.failure_count = 0
                self._stats.success_count = 0
                self._stats.state = CircuitState.CLOSED
                self._stats.half_open_calls = 0
        else:
            # Reset failure count on success in CLOSED state
            self._stats.failure_count = 0

    def _on_failure(self, error: Exception) -> None:
        """Handle failed call.

        Args:
            error: The exception that occurred.
        """
        self._stats.failure_count += 1
        self._stats.success_count = 0  # Reset success count on failure
        self._stats.last_failure_time = datetime.now(UTC)

        if self._stats.state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN immediately opens the circuit
            logger.warning(
                "Circuit breaker failed in half-open state, reopening",
                circuit_name=self._name,
                error_type=type(error).__name__,
                operation="CIRCUIT_REOPENED",
            )
            self._stats.state = CircuitState.OPEN
        elif self._stats.failure_count >= self._config.failure_threshold:
            logger.warning(
                "Circuit breaker opened after failures",
                circuit_name=self._name,
                failure_count=self._stats.failure_count,
                recovery_timeout=self._config.recovery_timeout,
                operation="CIRCUIT_OPENED",
            )
            self._stats.state = CircuitState.OPEN

    def _is_monitored_exception(self, error: Exception) -> bool:
        """Check if exception should trip the circuit.

        Args:
            error: The exception to check.

        Returns:
            True if exception should count as failure.
        """
        return isinstance(error, self._config.monitored_exceptions)

    async def __call__(
        self,
        command: Any,
        next_handler: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        """Execute command with circuit breaker protection.

        Args:
            command: The command to execute.
            next_handler: The next handler in the chain.

        Returns:
            Result from the handler.

        Raises:
            CircuitBreakerOpenError: If circuit is open.
        """
        command_type = type(command).__name__

        # Check if circuit is open
        if self._stats.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    "Circuit breaker entering half-open state",
                    circuit_name=self._name,
                    operation="CIRCUIT_HALF_OPEN",
                )
                self._stats.state = CircuitState.HALF_OPEN
                self._stats.half_open_calls = 0
                self._stats.success_count = 0
            else:
                recovery_time = self._stats.last_failure_time
                if recovery_time:
                    recovery_time += timedelta(seconds=self._config.recovery_timeout)

                raise CircuitBreakerOpenError(
                    message=f"Circuit breaker '{self._name}' is open for {command_type}",
                    recovery_time=recovery_time or datetime.now(UTC),
                    circuit_name=self._name,
                )

        # Check half-open limit
        if self._stats.state == CircuitState.HALF_OPEN:
            if self._stats.half_open_calls >= self._config.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    message=f"Circuit breaker '{self._name}' half-open limit reached for {command_type}",
                    recovery_time=datetime.now(UTC),
                    circuit_name=self._name,
                )
            self._stats.half_open_calls += 1

        # Execute command
        try:
            result = await next_handler(command)
            self._on_success()
            return result

        except Exception as e:
            if self._is_monitored_exception(e):
                self._on_failure(e)
            raise
