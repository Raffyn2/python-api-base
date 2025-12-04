"""Timeout pattern implementation.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.3**
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from core.base.patterns.result import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class TimeoutConfig:
    """Timeout configuration."""

    duration_seconds: float
    message: str = "Operation timed out"


class Timeout[T]:
    """Generic timeout wrapper.

    Type Parameters:
        T: The return type of the timed operation.
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
        except TimeoutError:
            return Err(TimeoutError(self._config.message))
