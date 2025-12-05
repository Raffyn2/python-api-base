"""Circuit breaker integration for gRPC clients.

This module provides circuit breaker wrapper for gRPC calls
to prevent cascading failures.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from grpc import StatusCode
from structlog import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3


class CircuitBreakerWrapper:
    """Circuit breaker wrapper for gRPC calls.
    
    Implements the circuit breaker pattern to prevent cascading
    failures when a service is unavailable.
    """

    def __init__(
        self,
        config: CircuitBreakerConfig | None = None,
        name: str = "default",
    ) -> None:
        """Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
            name: Name for logging
        """
        self._config = config or CircuitBreakerConfig()
        self._name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        self._check_state_transition()
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (allowing calls)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking calls)."""
        return self.state == CircuitState.OPEN

    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> T:
        """Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            
        Returns:
            The function result
            
        Raises:
            CircuitOpenError: If circuit is open
        """
        self._check_state_transition()
        
        if self._state == CircuitState.OPEN:
            logger.warning(
                "circuit_breaker_open",
                name=self._name,
                failure_count=self._failure_count,
            )
            raise CircuitOpenError(f"Circuit breaker {self._name} is open")

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self._config.half_open_max_calls:
                raise CircuitOpenError(f"Circuit breaker {self._name} half-open limit reached")
            self._half_open_calls += 1

        try:
            result = await func()
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            raise

    def _check_state_transition(self) -> None:
        """Check and perform state transitions."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time is not None:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self._config.recovery_timeout:
                    self._transition_to_half_open()

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        logger.info(
            "circuit_breaker_half_open",
            name=self._name,
        )

    def _on_success(self) -> None:
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._config.half_open_max_calls:
                self._reset()
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        
        if self._state == CircuitState.HALF_OPEN:
            self._open()
        elif self._failure_count >= self._config.failure_threshold:
            self._open()

    def _open(self) -> None:
        """Open the circuit."""
        self._state = CircuitState.OPEN
        logger.warning(
            "circuit_breaker_opened",
            name=self._name,
            failure_count=self._failure_count,
        )

    def _reset(self) -> None:
        """Reset circuit to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        logger.info(
            "circuit_breaker_closed",
            name=self._name,
        )


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class RetryInterceptor:
    """Retry interceptor with exponential backoff.
    
    Provides retry logic for gRPC calls with configurable
    backoff and jitter.
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
        backoff_multiplier: float = 2.0,
        jitter: float = 0.1,
    ) -> None:
        """Initialize retry interceptor.
        
        Args:
            max_retries: Maximum number of retries
            backoff_base: Base delay in seconds
            backoff_max: Maximum delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Jitter factor (0-1)
        """
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max
        self._backoff_multiplier = backoff_multiplier
        self._jitter = jitter

    async def execute_with_retry(
        self,
        func: Callable[[], Awaitable[T]],
        retryable_codes: set[StatusCode] | None = None,
    ) -> T:
        """Execute function with retry logic.
        
        Args:
            func: Async function to execute
            retryable_codes: Status codes that should trigger retry
            
        Returns:
            The function result
        """
        if retryable_codes is None:
            retryable_codes = {
                StatusCode.UNAVAILABLE,
                StatusCode.RESOURCE_EXHAUSTED,
                StatusCode.ABORTED,
            }

        last_exception: Exception | None = None
        
        for attempt in range(self._max_retries + 1):
            try:
                return await func()
            except Exception as exc:
                last_exception = exc
                
                # Check if retryable
                if not self._is_retryable(exc, retryable_codes):
                    raise
                
                if attempt < self._max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        "grpc_retry",
                        attempt=attempt + 1,
                        max_retries=self._max_retries,
                        delay=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry state")

    def _is_retryable(
        self,
        exc: Exception,
        retryable_codes: set[StatusCode],
    ) -> bool:
        """Check if exception is retryable."""
        if hasattr(exc, "code") and callable(exc.code):
            return exc.code() in retryable_codes
        return False

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        import random
        
        delay = self._backoff_base * (self._backoff_multiplier ** attempt)
        delay = min(delay, self._backoff_max)
        
        # Add jitter
        jitter_range = delay * self._jitter
        delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
