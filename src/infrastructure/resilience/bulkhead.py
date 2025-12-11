"""Bulkhead pattern implementation.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.5**
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, ParamSpec

from core.base.patterns.result import Err, Ok, Result

P = ParamSpec("P")


class BulkheadState(Enum):
    """Bulkhead state."""

    ACCEPTING = "accepting"
    REJECTING = "rejecting"


class BulkheadRejectedError(Exception):
    """Raised when bulkhead rejects a request."""

    def __init__(self, name: str, message: str = "Bulkhead rejected request") -> None:
        self.name = name
        super().__init__(f"{message}: {name}")


@dataclass(slots=True)
class BulkheadConfig:
    """Bulkhead configuration for resource isolation."""

    max_concurrent: int = 10
    max_wait_seconds: float = 5.0


@dataclass(slots=True)
class BulkheadStats:
    """Statistics for a bulkhead."""

    name: str
    max_concurrent: int
    current_concurrent: int = 0
    total_accepted: int = 0
    total_rejected: int = 0
    total_completed: int = 0
    total_failed: int = 0

    @property
    def available_permits(self) -> int:
        """Get available permits."""
        return self.max_concurrent - self.current_concurrent

    @property
    def utilization(self) -> float:
        """Get utilization ratio."""
        if self.max_concurrent == 0:
            return 0.0
        return self.current_concurrent / self.max_concurrent

    @property
    def success_rate(self) -> float:
        """Get success rate."""
        total = self.total_completed + self.total_failed
        if total == 0:
            return 0.0
        return self.total_completed / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "current_concurrent": self.current_concurrent,
            "available_permits": self.available_permits,
            "utilization": self.utilization,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "success_rate": self.success_rate,
        }


class Bulkhead[T]:
    """Generic bulkhead for resource isolation.

    Type Parameters:
        T: The return type of isolated operations.
    """

    def __init__(
        self,
        name: str = "default",
        max_concurrent: int = 10,
        max_wait_seconds: float = 5.0,
        config: BulkheadConfig | None = None,
    ) -> None:
        if config:
            self._config = config
        else:
            self._config = BulkheadConfig(
                max_concurrent=max_concurrent,
                max_wait_seconds=max_wait_seconds,
            )
        self._name = name
        self._semaphore = asyncio.Semaphore(self._config.max_concurrent)
        self._rejected_count = 0
        self._accepted_count = 0
        self._completed_count = 0
        self._failed_count = 0
        self._current_concurrent = 0

    @property
    def name(self) -> str:
        """Get bulkhead name."""
        return self._name

    @property
    def rejected_count(self) -> int:
        """Get count of rejected calls."""
        return self._rejected_count

    @property
    def state(self) -> BulkheadState:
        """Get current bulkhead state."""
        if self._current_concurrent >= self._config.max_concurrent:
            return BulkheadState.REJECTING
        return BulkheadState.ACCEPTING

    @property
    def stats(self) -> BulkheadStats:
        """Get bulkhead statistics (property alias)."""
        return self.get_stats()

    def get_stats(self) -> BulkheadStats:
        """Get bulkhead statistics."""
        return BulkheadStats(
            name=self._name,
            max_concurrent=self._config.max_concurrent,
            current_concurrent=self._current_concurrent,
            total_accepted=self._accepted_count,
            total_rejected=self._rejected_count,
            total_completed=self._completed_count,
            total_failed=self._failed_count,
        )

    async def acquire(self) -> bool:
        """Acquire a permit from the bulkhead."""
        try:
            acquired = await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self._config.max_wait_seconds,
            )
            if acquired:
                self._current_concurrent += 1
                self._accepted_count += 1
                return True
            self._rejected_count += 1
            return False
        except TimeoutError:
            self._rejected_count += 1
            return False

    async def release(self) -> None:
        """Release a permit back to the bulkhead."""
        if self._current_concurrent > 0:
            self._current_concurrent -= 1
            self._semaphore.release()

    @asynccontextmanager
    async def acquire_context(self) -> AsyncIterator[None]:
        """Context manager for acquiring and releasing permits."""
        acquired = await self.acquire()
        if not acquired:
            raise BulkheadRejectedError(self._name)
        try:
            yield
            self._completed_count += 1
        except Exception:
            self._failed_count += 1
            raise
        finally:
            await self.release()

    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute with bulkhead isolation.

        Returns:
            Result of the function.

        Raises:
            BulkheadRejectedError: If bulkhead rejects the request.
        """
        async with self.acquire_context():
            return await func(*args, **kwargs)

    async def execute_safe(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> Result[T, Exception]:
        """Execute with bulkhead isolation (Result pattern).

        Returns:
            Ok with result or Err if rejected.
        """
        try:
            result = await self.execute(func, *args, **kwargs)
            return Ok(result)
        except Exception as e:
            return Err(e)


class BulkheadRegistry:
    """Registry for managing multiple bulkheads."""

    def __init__(self) -> None:
        self._bulkheads: dict[str, Bulkhead[Any]] = {}

    def register(
        self,
        name: str,
        max_concurrent: int = 10,
        max_wait_seconds: float = 5.0,
    ) -> Bulkhead[Any]:
        """Register a new bulkhead."""
        bulkhead: Bulkhead[Any] = Bulkhead(
            name=name,
            max_concurrent=max_concurrent,
            max_wait_seconds=max_wait_seconds,
        )
        self._bulkheads[name] = bulkhead
        return bulkhead

    def get(self, name: str) -> Bulkhead[Any] | None:
        """Get a bulkhead by name."""
        return self._bulkheads.get(name)

    def get_or_create(
        self,
        name: str,
        max_concurrent: int = 10,
        max_wait_seconds: float = 5.0,
    ) -> Bulkhead[Any]:
        """Get existing or create new bulkhead."""
        if name in self._bulkheads:
            return self._bulkheads[name]
        return self.register(name, max_concurrent, max_wait_seconds)

    def list_names(self) -> list[str]:
        """List all bulkhead names."""
        return list(self._bulkheads.keys())

    def get_all_stats(self) -> dict[str, BulkheadStats]:
        """Get stats for all bulkheads."""
        return {name: bh.get_stats() for name, bh in self._bulkheads.items()}


def bulkhead[R](
    name: str,
    max_concurrent: int = 10,
    max_wait_seconds: float = 5.0,
    registry: BulkheadRegistry | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator to apply bulkhead pattern to async function."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        _registry = registry or BulkheadRegistry()
        _bulkhead = _registry.get_or_create(name, max_concurrent, max_wait_seconds)

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async def call() -> R:
                return await func(*args, **kwargs)

            return await _bulkhead.execute(call)

        return wrapper

    return decorator
