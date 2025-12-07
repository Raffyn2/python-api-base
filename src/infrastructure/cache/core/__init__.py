"""Cache core components.

Contains cache configuration, models, protocols, policies, and serializers.

**Feature: infrastructure-restructuring-2025**
**Feature: test-coverage-80-percent-v2**
"""

from infrastructure.cache.core.config import CacheConfig
from infrastructure.cache.core.models import CacheEntry, CacheKey, CacheStats
from infrastructure.cache.core.protocols import CacheProvider
from infrastructure.cache.core.serializers import JsonSerializer, Serializer

__all__ = [
    "CacheConfig",
    "CacheEntry",
    "CacheKey",
    "CacheProvider",
    "CacheStats",
    "JsonSerializer",
    "Serializer",
]
