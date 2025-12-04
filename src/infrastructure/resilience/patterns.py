"""Generic resilience patterns with PEP 695 type parameters.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5**
**Improvement: P2-2 - Added OpenTelemetry metrics to Circuit Breaker**
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from core.base.patterns.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(frozen=True, slots=True)
class CircuitBreakerConfig[TThreshold]:
    """Generic circuit breaker configuration.

    Type Parameters:
        TThreshold: Type for failure threshold (int, float, or custom).

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.1**
    """

    failure_threshold: TThreshold
    success_threshold: int = 3
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 3


class CircuitBreaker[TConfig: CircuitBreakerConfig]:
    """Generic circuit breaker with typed configuration.

    Type Parameters:
        TConfig: Configuration type extending CircuitBreakerConfig.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.1**
    **Improvement: P2-2 - Added OpenTelemetry metrics**
    """

    def __init__(self, config: TConfig, name: str = "default") -> None:
        self._config = config
        self._name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._half_open_calls = 0

        # Initialize metrics
        self._meter: Any = None
        self._state_gauge: Any = None
        self._calls_counter: Any = None
        self._failures_counter: Any = None
        self._state_transitions_counter: Any = None
        self._execution_histogram: Any = None
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """Initialize OpenTelemetry metrics for circuit breaker."""
        try:
            from opentelemetry import metrics

            self._meter = metrics.get_meter("infrastructure.resilience")

            # State gauge - current circuit state
            self._state_gauge = self._meter.create_observable_gauge(
                name="circuit_breaker.state",
                description="Current circuit breaker state (0=closed, 1=half_open, 2=open)",
                callbacks=[self._observe_state],
            )

            # Calls counter - total calls attempted
            self._calls_counter = self._meter.create_counter(
                name="circuit_breaker.calls",
                description="Total number of calls attempted through circuit breaker",
                unit="1",
            )

            # Failures counter - failed calls
            self._failures_counter = self._meter.create_counter(
                name="circuit_breaker.failures",
                description="Number of failed calls",
                unit="1",
            )

            # State transitions counter - circuit state changes
            self._state_transitions_counter = self._meter.create_counter(
                name="circuit_breaker.state_transitions",
                description="Number of circuit state transitions",
                unit="1",
            )

            # Execution histogram - call duration
            self._execution_histogram = self._meter.create_histogram(
                name="circuit_breaker.execution_duration",
                description="Duration of calls through circuit breaker",
                unit="ms",
            )

            logger.info(
                f"Circuit breaker metrics initialized",
                extra={"name": self._name}
            )
        except ImportError:
            logger.debug("OpenTelemetry not available, metrics disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize circuit breaker metrics: {e}")

    def _observe_state(self) -> list:
        """Callback for observing current circuit state."""
        state_value = {
            CircuitState.CLOSED: 0,
            CircuitState.HALF_OPEN: 1,
            CircuitState.OPEN: 2,
        }[self._state]

        from opentelemetry.metrics import Observation
        return [Observation(state_value, {"circuit": self._name, "state": self._state.value})]

    def _record_state_transition(self, from_state: CircuitState, to_state: CircuitState) -> None:
        """Record circuit state transition metric."""
        if self._state_transitions_counter:
            self._state_transitions_counter.add(
                1,
                {
                    "circuit": self._name,
                    "from_state": from_state.value,
                    "to_state": to_state.value,
                },
            )
        logger.info(
            f"Circuit breaker state transition",
            extra={
                "circuit": self._name,
                "from_state": from_state.value,
                "to_state": to_state.value,
            }
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        self._check_timeout()
        return self._state

    def _check_timeout(self) -> None:
        """Check if timeout has passed to transition from OPEN to HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = datetime.now() - self._last_failure_time
            if elapsed.total_seconds() >= self._config.timeout_seconds:
                old_state = self._state
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                self._record_state_transition(old_state, self._state)

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._config.success_threshold:
                old_state = self._state
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._record_state_transition(old_state, self._state)
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        # Record failure metric
        if self._failures_counter:
            self._failures_counter.add(1, {"circuit": self._name, "state": self._state.value})

        self._failure_count += 1
        self._last_failure_time = datetime.now()
        threshold = self._config.failure_threshold

        old_state = self._state
        state_changed = False

        if isinstance(threshold, int) and self._failure_count >= threshold:
            self._state = CircuitState.OPEN
            state_changed = True
        elif self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            state_changed = True

        if state_changed:
            self._record_state_transition(old_state, self._state)

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        self._check_timeout()
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self._config.half_open_max_calls
        return False

    async def execute[T](
        self,
        func: Callable[[], Awaitable[T]],
    ) -> Result[T, Exception]:
        """Execute function with circuit breaker protection.

        Returns:
            Ok with result or Err with exception.
        """
        # Record call attempt
        if self._calls_counter:
            self._calls_counter.add(1, {"circuit": self._name, "state": self._state.value})

        if not self.can_execute():
            return Err(Exception("Circuit is open"))

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1

        # Track execution duration
        start_time = datetime.now()

        try:
            result = await func()
            self.record_success()

            # Record execution duration on success
            if self._execution_histogram:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                self._execution_histogram.record(
                    duration_ms,
                    {"circuit": self._name, "result": "success", "state": self._state.value}
                )

            return Ok(result)
        except Exception as e:
            self.record_failure()

            # Record execution duration on failure
            if self._execution_histogram:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                self._execution_histogram.record(
                    duration_ms,
                    {"circuit": self._name, "result": "failure", "state": self._state.value}
                )

            return Err(e)


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Configuration for retry behavior.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.2**
    """

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@runtime_checkable
class BackoffStrategy(Protocol):
    """Protocol for backoff strategies."""

    def get_delay(self, attempt: int) -> float:
        """Get delay for given attempt number."""
        ...


class ExponentialBackoff:
    """Exponential backoff with optional jitter.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.2**
    """

    def __init__(self, config: RetryConfig) -> None:
        self._config = config

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff."""
        delay = self._config.base_delay_seconds * (
            self._config.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self._config.max_delay_seconds)
        if self._config.jitter:
            delay = delay * (0.5 + random.random())
        return delay


class Retry[T]:
    """Generic retry wrapper with typed result.

    Type Parameters:
        T: The return type of the retried operation.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.2**
    """

    def __init__(
        self,
        config: RetryConfig | None = None,
        backoff: BackoffStrategy | None = None,
    ) -> None:
        self._config = config or RetryConfig()
        self._backoff = backoff or ExponentialBackoff(self._config)

    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> Result[T, Exception]:
        """Execute with retry logic.

        Args:
            func: Async function to execute.
            retryable_exceptions: Exception types that trigger retry.

        Returns:
            Ok with result or Err with last exception.
        """
        last_error: Exception | None = None

        for attempt in range(1, self._config.max_attempts + 1):
            try:
                result = await func()
                return Ok(result)
            except retryable_exceptions as e:
                last_error = e
                if attempt < self._config.max_attempts:
                    delay = self._backoff.get_delay(attempt)
                    await asyncio.sleep(delay)

        return Err(last_error or Exception("All retries failed"))


@dataclass(frozen=True, slots=True)
class TimeoutConfig:
    """Timeout configuration."""

    duration_seconds: float
    message: str = "Operation timed out"


class Timeout[T]:
    """Generic timeout wrapper.

    Type Parameters:
        T: The return type of the timed operation.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.3**
    """

    def __init__(self, config: TimeoutConfig) -> None:
        self._config = config

    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> Result[T, TimeoutError]:
        """Execute with timeout.

        Returns:
            Ok with result or Err with TimeoutError.
        """
        try:
            result = await asyncio.wait_for(
                func(),
                timeout=self._config.duration_seconds,
            )
            return Ok(result)
        except asyncio.TimeoutError:
            return Err(TimeoutError(self._config.message))


class Fallback[T, TFallback]:
    """Generic fallback pattern for graceful degradation.

    Type Parameters:
        T: Primary operation return type.
        TFallback: Fallback value type.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.4**
    """

    def __init__(
        self,
        fallback_value: TFallback | None = None,
        fallback_func: Callable[[], Awaitable[TFallback]] | None = None,
    ) -> None:
        self._fallback_value = fallback_value
        self._fallback_func = fallback_func

    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> T | TFallback:
        """Execute with fallback on failure.

        Returns:
            Primary result or fallback value.
        """
        try:
            return await func()
        except Exception:
            if self._fallback_func:
                return await self._fallback_func()
            if self._fallback_value is not None:
                return self._fallback_value
            raise


@dataclass
class BulkheadConfig:
    """Bulkhead configuration for resource isolation."""

    max_concurrent: int = 10
    max_wait_seconds: float = 5.0


class Bulkhead[T]:
    """Generic bulkhead for resource isolation.

    Type Parameters:
        T: The return type of isolated operations.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 16.5**
    """

    def __init__(self, config: BulkheadConfig) -> None:
        self._config = config
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._rejected_count = 0

    @property
    def rejected_count(self) -> int:
        """Get count of rejected calls."""
        return self._rejected_count

    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> Result[T, Exception]:
        """Execute with bulkhead isolation.

        Returns:
            Ok with result or Err if rejected.
        """
        try:
            acquired = await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self._config.max_wait_seconds,
            )
            if not acquired:
                self._rejected_count += 1
                return Err(Exception("Bulkhead rejected: max concurrent reached"))
        except asyncio.TimeoutError:
            self._rejected_count += 1
            return Err(Exception("Bulkhead rejected: wait timeout"))

        try:
            result = await func()
            return Ok(result)
        finally:
            self._semaphore.release()
