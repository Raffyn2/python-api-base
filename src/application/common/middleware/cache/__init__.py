"""Cache middleware and utilities.

Provides caching functionality for query results and cache invalidation strategies.

**Feature: application-layer-improvements-2025**
"""

from application.common.middleware.cache.cache_invalidation import (
    CacheInvalidationMiddleware,
    CacheInvalidationStrategy,
    CompositeCacheInvalidationStrategy,
    InvalidationRule,
    ItemCacheInvalidationStrategy,
    UserCacheInvalidationStrategy,
    create_entity_specific_pattern,
    create_query_type_pattern,
)
from application.common.middleware.cache.query_cache import (
    InMemoryQueryCache,
    QueryCache,
    QueryCacheConfig,
    QueryCacheMiddleware,
)

__all__ = [
    # Cache Invalidation
    "CacheInvalidationMiddleware",
    "CacheInvalidationStrategy",
    "CompositeCacheInvalidationStrategy",
    # Query Cache
    "InMemoryQueryCache",
    "InvalidationRule",
    "ItemCacheInvalidationStrategy",
    "QueryCache",
    "QueryCacheConfig",
    "QueryCacheMiddleware",
    "UserCacheInvalidationStrategy",
    "create_entity_specific_pattern",
    "create_query_type_pattern",
]
