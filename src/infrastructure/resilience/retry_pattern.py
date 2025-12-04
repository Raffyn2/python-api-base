"""Retry pattern implementation.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.2**
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.base.patterns.result import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Configuration for retry behavior."""

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
    """Exponential backoff with optional jitter."""

    def __init__(self, config: RetryConfig) -> None:
        self._config = config

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff."""
        delay = self._config.base_delay_seconds * (
            self._config.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self._config.max_delay_seconds)
        if self._config.jitter:
            delay = delay * (0.5 + random.random())  # noqa: S311
        return delay


class Retry[T]:
    """Generic retry wrapper with typed result.

    Type Parameters:
        T: The return type of the retried operation.
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
