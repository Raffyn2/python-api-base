"""Cache protocols re-export.

**Feature: test-coverage-80-percent-v2**
**Validates: Requirements 2.1, 2.3**

Re-exports cache protocols from core submodule for backward compatibility.
"""

from infrastructure.cache.core.protocols import (
    CacheEntry,
    CacheKey,
    CacheProvider,
    JsonSerializer,
    Serializer,
)

__all__ = [
    "CacheEntry",
    "CacheKey",
    "CacheProvider",
    "JsonSerializer",
    "Serializer",
]
