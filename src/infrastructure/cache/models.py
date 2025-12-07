"""Cache models re-export.

**Feature: test-coverage-80-percent-v2**
**Validates: Requirements 2.1, 2.2**

Re-exports cache models from core submodule for backward compatibility.
"""

from infrastructure.cache.core.models import (
    CacheEntry,
    CacheKey,
    CacheStats,
)

__all__ = [
    "CacheEntry",
    "CacheKey",
    "CacheStats",
]
