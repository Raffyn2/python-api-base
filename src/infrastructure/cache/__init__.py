"""Cache infrastructure.

**Refactored: 2025 - Split into focused modules**
**Feature: infrastructure-modules-integration-analysis**
**Feature: test-coverage-80-percent-v2**
"""

from infrastructure.cache.core.models import CacheStats
from infrastructure.cache.core.protocols import (
    CacheEntry,
    CacheKey,
    CacheProvider,
    JsonSerializer,
)
from infrastructure.cache.decorators import (
    cached,
    get_default_cache,
    invalidate_cache,
    invalidate_pattern,
    set_default_cache,
)
from infrastructure.cache.providers.local import LRUCache
from infrastructure.cache.providers.memory import InMemoryCacheProvider
from infrastructure.cache.providers.redis import RedisCacheProvider
from infrastructure.cache.repository import (
    RepositoryCacheConfig,
    cached_repository,
    invalidate_repository_cache,
)

__all__ = [
    "CacheEntry",
    "CacheKey",
    "CacheProvider",
    "CacheStats",
    "InMemoryCacheProvider",
    "JsonSerializer",
    "LRUCache",
    "RedisCacheProvider",
    "RepositoryCacheConfig",
    # Decorators
    "cached",
    "cached_repository",
    "get_default_cache",
    "invalidate_cache",
    "invalidate_pattern",
    "invalidate_repository_cache",
    "set_default_cache",
]
