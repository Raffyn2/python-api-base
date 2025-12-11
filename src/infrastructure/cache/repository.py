"""Repository caching decorator with automatic invalidation.

**Feature: repository-caching**
**Validates: Requirements for performant data access with automatic cache invalidation**

Provides a decorator that:
- Caches read operations (get_by_id, get_all, exists)
- Invalidates cache on mutations (create, update, delete)
- Uses entity type name for cache key namespacing
- Supports configurable TTL per entity type
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

import structlog

from infrastructure.cache.protocols import CacheProvider

logger = structlog.get_logger(__name__)

T = TypeVar("T")

# Methods to cache (read operations)
CACHED_METHODS: frozenset[str] = frozenset({"get_by_id", "get_all", "exists", "get_page"})

# Methods that invalidate cache (write operations)
INVALIDATING_METHODS: frozenset[str] = frozenset({"create", "update", "delete", "create_many"})


class RepositoryCacheConfig:
    """Configuration for repository caching.

    Attributes:
        ttl: Time-to-live in seconds (default: 300 = 5 minutes).
        enabled: Whether caching is enabled (default: True).
        key_prefix: Prefix for all cache keys (default: "repo").
        log_hits: Whether to log cache hits (default: True in debug).
        log_misses: Whether to log cache misses (default: False).
    """

    def __init__(
        self,
        ttl: int = 300,
        enabled: bool = True,
        key_prefix: str = "repo",
        log_hits: bool = False,
        log_misses: bool = False,
    ) -> None:
        self.ttl = ttl
        self.enabled = enabled
        self.key_prefix = key_prefix
        self.log_hits = log_hits
        self.log_misses = log_misses


def _get_entity_name(repository: Any) -> str:
    """Extract entity name from repository class.

    Attempts to extract from:
    1. repository.__class__.__name__ (e.g., "UserRepository" -> "User")
    2. Fallback to class name if pattern doesn't match

    Args:
        repository: The repository instance.

    Returns:
        Entity name for cache key namespacing.
    """
    class_name = repository.__class__.__name__
    if class_name.endswith("Repository"):
        # Remove "Repository" suffix
        return class_name[:-10]
    return class_name


def _make_cache_key(prefix: str, entity_name: str, method_name: str, *args: Any, **kwargs: Any) -> str:
    """Generate cache key for repository method.

    Format: {prefix}:{entity_name}:{method_name}:{arg_hash}

    Args:
        prefix: Cache key prefix (e.g., "repo").
        entity_name: Entity name (e.g., "User").
        method_name: Method name (e.g., "get_by_id").
        *args: Method positional arguments.
        **kwargs: Method keyword arguments.

    Returns:
        Cache key string.
    """
    # For get_by_id, use the ID directly in the key
    if method_name == "get_by_id" and args:
        return f"{prefix}:{entity_name}:{method_name}:{args[0]}"

    # For other methods, use a hash of all args/kwargs
    arg_str = "_".join(str(arg) for arg in args)
    kwarg_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    combined = f"{arg_str}_{kwarg_str}" if kwarg_str else arg_str

    return f"{prefix}:{entity_name}:{method_name}:{combined}"


def _get_invalidation_pattern(prefix: str, entity_name: str) -> str:
    """Get pattern for invalidating all cache entries for an entity type.

    Args:
        prefix: Cache key prefix.
        entity_name: Entity name.

    Returns:
        Pattern string (e.g., "repo:User:*").
    """
    return f"{prefix}:{entity_name}:*"


async def _try_get_cached(
    cache_provider: CacheProvider[Any],
    cache_key: str,
) -> tuple[Any, bool]:
    """Try to get value from cache.

    Returns:
        Tuple of (value, found). If error occurs, returns (None, False).
    """
    try:
        cached_value = await cache_provider.get(cache_key)
        return (cached_value, cached_value is not None)
    except Exception:
        logger.exception(
            "Cache read failed, falling back to database",
            cache_key=cache_key,
        )
        return (None, False)


async def _try_set_cached(
    cache_provider: CacheProvider[Any],
    cache_key: str,
    value: Any,
    ttl: int,
) -> None:
    """Try to set value in cache. Logs warning on failure."""
    try:
        await cache_provider.set(cache_key, value, ttl)
    except Exception:
        logger.exception("Cache write failed", cache_key=cache_key)


async def _try_invalidate_cache(
    cache_provider: CacheProvider[Any],
    pattern: str,
    entity_name: str,
    method_name: str,
) -> None:
    """Try to invalidate cache by pattern. Logs warning on failure."""
    try:
        count = await cache_provider.clear_pattern(pattern)
        logger.debug(
            "Cache invalidated after mutation",
            entity=entity_name,
            method=method_name,
            pattern=pattern,
            keys_cleared=count,
        )
    except Exception:
        logger.exception("Cache invalidation failed", pattern=pattern)


def _create_cached_method(
    cache_provider: CacheProvider[Any],
    config: RepositoryCacheConfig,
    method_name: str,
    original_method: Callable[..., Any],
) -> Callable[..., Any]:
    """Create cached version of a read method."""

    @functools.wraps(original_method)
    async def cached_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        entity_name = _get_entity_name(self)
        cache_key = _make_cache_key(config.key_prefix, entity_name, method_name, *args, **kwargs)

        cached_value, found = await _try_get_cached(cache_provider, cache_key)
        if found:
            if config.log_hits:
                logger.info(
                    "Repository cache HIT",
                    entity=entity_name,
                    method=method_name,
                    cache_key=cache_key,
                )
            return cached_value

        if config.log_misses:
            logger.debug(
                "Repository cache MISS",
                entity=entity_name,
                method=method_name,
                cache_key=cache_key,
            )

        result = await original_method(self, *args, **kwargs)

        if result is not None:
            await _try_set_cached(cache_provider, cache_key, result, config.ttl)

        return result

    return cached_wrapper


def _create_invalidating_method(
    cache_provider: CacheProvider[Any],
    config: RepositoryCacheConfig,
    method_name: str,
    original_method: Callable[..., Any],
) -> Callable[..., Any]:
    """Create version of write method that invalidates cache."""

    @functools.wraps(original_method)
    async def invalidating_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        result = await original_method(self, *args, **kwargs)

        entity_name = _get_entity_name(self)
        pattern = _get_invalidation_pattern(config.key_prefix, entity_name)
        await _try_invalidate_cache(cache_provider, pattern, entity_name, method_name)

        return result

    return invalidating_wrapper


def _wrap_repository_methods[R](
    repository_class: type[R],
    cache_provider: CacheProvider[Any],
    config: RepositoryCacheConfig,
) -> dict[str, Callable[..., Any]]:
    """Wrap repository methods with caching/invalidation logic.

    Returns:
        Dictionary of original methods for testing/debugging.
    """
    original_methods: dict[str, Callable[..., Any]] = {}

    for attr_name in dir(repository_class):
        if attr_name.startswith("_"):
            continue

        attr = getattr(repository_class, attr_name)
        if not inspect.iscoroutinefunction(attr):
            continue

        original_methods[attr_name] = attr

        if attr_name in CACHED_METHODS:
            wrapped = _create_cached_method(cache_provider, config, attr_name, attr)
            setattr(repository_class, attr_name, wrapped)
        elif attr_name in INVALIDATING_METHODS:
            wrapped = _create_invalidating_method(cache_provider, config, attr_name, attr)
            setattr(repository_class, attr_name, wrapped)

    return original_methods


def cached_repository[R](
    cache_provider: CacheProvider[Any],
    config: RepositoryCacheConfig | None = None,
) -> Callable[[type[R]], type[R]]:
    """Decorator to add caching to repository classes.

    Automatically caches read operations and invalidates on mutations.

    **Read Operations (Cached):**
    - get_by_id, get_all, exists, get_page

    **Write Operations (Invalidate Cache):**
    - create, update, delete, create_many

    Args:
        cache_provider: Cache provider instance (Redis, InMemory, etc.).
        config: Optional configuration (TTL, logging, etc.).

    Returns:
        Decorated repository class with caching.

    Example:
        >>> @cached_repository(cache, RepositoryCacheConfig(ttl=600))
        ... class UserRepository(IRepository):
        ...     async def get_by_id(self, id: str) -> User | None:
        ...         return await self._fetch_from_db(id)
    """
    effective_config = config or RepositoryCacheConfig()

    def class_decorator(repository_class: type[R]) -> type[R]:
        if not effective_config.enabled:
            return repository_class

        original_methods = _wrap_repository_methods(repository_class, cache_provider, effective_config)

        repository_class._original_methods = original_methods  # type: ignore
        repository_class._cache_config = effective_config  # type: ignore

        return repository_class

    return class_decorator


# Convenience function for manual cache invalidation
async def invalidate_repository_cache(
    cache_provider: CacheProvider[Any],
    entity_name: str,
    key_prefix: str = "repo",
) -> int:
    """Manually invalidate all cache entries for an entity type.

    Useful for external cache invalidation scenarios.

    Args:
        cache_provider: Cache provider instance.
        entity_name: Entity name (e.g., "User").
        key_prefix: Cache key prefix (default: "repo").

    Returns:
        Number of cache keys cleared.

    Example:
        >>> # Invalidate all User cache entries
        >>> count = await invalidate_repository_cache(cache, "User")
        >>> print(f"Cleared {count} User cache entries")
    """
    pattern = _get_invalidation_pattern(key_prefix, entity_name)
    count = await cache_provider.clear_pattern(pattern)
    logger.info(
        "Manual repository cache invalidation",
        entity=entity_name,
        pattern=pattern,
        keys_cleared=count,
    )
    return count
