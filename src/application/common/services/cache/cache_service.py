"""Cache service for use cases.

Provides centralized cache operations with consistent error handling.

**Feature: application-layer-code-review-2025**
**Extracted from: examples/item/use_case.py**
"""

from typing import Any, Protocol

import structlog

logger = structlog.get_logger(__name__)


class CacheProtocol(Protocol):
    """Protocol for cache clients."""

    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...


class CacheService:
    """Service for cache operations.

    Centralizes cache operations with consistent error handling
    and key generation.

    Example:
        >>> cache_service = CacheService(cache_client, prefix="items")
        >>> await cache_service.get("123")  # Gets "items:123"
        >>> await cache_service.invalidate("123", invalidate_list=True)
    """

    def __init__(
        self,
        cache: CacheProtocol | None = None,
        prefix: str = "",
        list_key: str = "list",
    ) -> None:
        """Initialize cache service.

        Args:
            cache: Optional cache client.
            prefix: Key prefix for all cache operations.
            list_key: Key suffix for list cache (default: "list").
        """
        self._cache = cache
        self._prefix = prefix
        self._list_key = list_key

    @property
    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._cache is not None

    def _make_key(self, key: str) -> str:
        """Generate prefixed cache key."""
        if self._prefix:
            return f"{self._prefix}:{key}"
        return key

    def _list_cache_key(self) -> str:
        """Generate list cache key."""
        return self._make_key(self._list_key)

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key (will be prefixed).

        Returns:
            Cached value or None if not found.
        """
        if not self._cache:
            return None

        try:
            return await self._cache.get(self._make_key(key))
        except Exception:
            logger.warning("Cache get failed for %s", key, exc_info=True)
            return None

    async def set(self, key: str, value: Any, ttl: int | None = 300) -> None:
        """Set value in cache.

        Args:
            key: Cache key (will be prefixed).
            value: Value to cache.
            ttl: Time-to-live in seconds (default: 300).
        """
        if not self._cache:
            return

        try:
            await self._cache.set(self._make_key(key), value, ttl)
        except Exception:
            logger.warning("Cache set failed for %s", key, exc_info=True)

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key (will be prefixed).
        """
        if not self._cache:
            return

        try:
            await self._cache.delete(self._make_key(key))
        except Exception:
            logger.warning("Cache delete failed for %s", key, exc_info=True)

    async def invalidate(
        self,
        key: str,
        *,
        invalidate_list: bool = True,
    ) -> None:
        """Invalidate cache for key and optionally list.

        Args:
            key: Cache key (will be prefixed).
            invalidate_list: If True, also invalidate list cache.
        """
        await self.delete(key)
        if invalidate_list:
            await self.delete(self._list_key)
