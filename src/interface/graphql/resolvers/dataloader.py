"""DataLoader for N+1 query prevention.

Implements the DataLoader pattern for batching and caching database queries.
Use with Strawberry GraphQL resolvers to prevent N+1 query problems.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 20.5**

Example:
    async def batch_load_users(ids: list[str]) -> list[User | None]:
        users = await user_repo.get_many(ids)
        user_map = {u.id: u for u in users}
        return [user_map.get(id) for id in ids]

    loader = DataLoader(batch_load_users)
    user = await loader.load("user-123")
"""

import asyncio
from collections.abc import Awaitable, Callable, Hashable
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# Constants
_DEFAULT_BATCH_SIZE = 100
_MAX_BATCH_SIZE = 1000
_MIN_BATCH_SIZE = 1


@dataclass(slots=True)
class DataLoaderConfig:
    """DataLoader configuration.

    Attributes:
        batch_size: Maximum keys per batch (1-1000, default 100).
        cache: Enable caching of loaded values.
        batch_delay_ms: Delay before dispatching batch (allows grouping).
    """

    batch_size: int = _DEFAULT_BATCH_SIZE
    cache: bool = True
    batch_delay_ms: float = 0.0

    def __post_init__(self) -> None:
        """Validate configuration."""
        self.batch_size = max(_MIN_BATCH_SIZE, min(self.batch_size, _MAX_BATCH_SIZE))


@dataclass(slots=True)
class _PendingLoad[TKey, TValue]:
    """Internal: Pending load request."""

    key: TKey
    future: asyncio.Future[TValue | None] = field(default_factory=asyncio.Future)


class DataLoader[TKey: Hashable, TValue]:
    """Generic DataLoader for N+1 prevention.

    Batches multiple load requests into a single batch function call.
    Optionally caches results to avoid redundant loads.

    Type Parameters:
        TKey: The key type for loading (must be hashable).
        TValue: The value type returned.

    **Feature: python-api-base-2025-generics-audit**
    **Validates: Requirements 20.5**
    """

    def __init__(
        self,
        batch_fn: Callable[[list[TKey]], Awaitable[list[TValue | None]]],
        config: DataLoaderConfig | None = None,
    ) -> None:
        """Initialize DataLoader.

        Args:
            batch_fn: Async function that loads values for a list of keys.
                      Must return values in the same order as keys.
            config: Optional configuration.
        """
        self._batch_fn = batch_fn
        self._config = config or DataLoaderConfig()
        self._cache: dict[TKey, TValue] = {}
        self._pending: list[_PendingLoad[TKey, TValue]] = []
        self._dispatch_scheduled = False
        self._background_tasks: set[asyncio.Task[None]] = set()

    async def load(self, key: TKey) -> TValue | None:
        """Load a single value by key.

        Args:
            key: The key to load.

        Returns:
            The loaded value or None if not found.
        """
        # Check cache first
        if self._config.cache and key in self._cache:
            return self._cache[key]

        # Check if already pending
        for pending in self._pending:
            if pending.key == key:
                return await pending.future

        # Create pending load
        pending_load: _PendingLoad[TKey, TValue] = _PendingLoad(key=key)
        self._pending.append(pending_load)

        # Schedule dispatch if not already scheduled
        if not self._dispatch_scheduled:
            self._dispatch_scheduled = True
            asyncio.get_event_loop().call_soon(lambda: asyncio.create_task(self._dispatch()))

        return await pending_load.future

    async def load_many(self, keys: list[TKey]) -> list[TValue | None]:
        """Load multiple values by keys.

        Args:
            keys: The keys to load.

        Returns:
            List of loaded values (or None for missing).
        """
        return await asyncio.gather(*[self.load(key) for key in keys])

    async def _dispatch(self) -> None:
        """Dispatch batch load."""
        # Optional delay to allow more requests to batch
        if self._config.batch_delay_ms > 0:
            await asyncio.sleep(self._config.batch_delay_ms / 1000)

        self._dispatch_scheduled = False

        if not self._pending:
            return

        # Take pending loads up to batch size
        batch = self._pending[: self._config.batch_size]
        self._pending = self._pending[self._config.batch_size :]

        keys = [p.key for p in batch]

        try:
            values = await self._batch_fn(keys)

            if len(values) != len(keys):
                logger.error(
                    "dataloader_batch_size_mismatch",
                    expected=len(keys),
                    received=len(values),
                )
                # Fill missing with None
                values = list(values) + [None] * (len(keys) - len(values))

            for pending, value in zip(batch, values, strict=True):
                if value is not None and self._config.cache:
                    self._cache[pending.key] = value
                pending.future.set_result(value)

        except Exception as e:
            logger.exception("dataloader_batch_failed")
            for pending in batch:
                if not pending.future.done():
                    pending.future.set_exception(e)

        # Schedule next dispatch if more pending
        if self._pending and not self._dispatch_scheduled:
            self._dispatch_scheduled = True
            task = asyncio.create_task(self._dispatch())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    def clear(self, key: TKey | None = None) -> None:
        """Clear cache for key or all.

        Args:
            key: Specific key to clear, or None to clear all.
        """
        if key is None:
            self._cache.clear()
        elif key in self._cache:
            del self._cache[key]

    def prime(self, key: TKey, value: TValue) -> None:
        """Prime cache with a value.

        Args:
            key: The key to prime.
            value: The value to cache.
        """
        if self._config.cache:
            self._cache[key] = value
