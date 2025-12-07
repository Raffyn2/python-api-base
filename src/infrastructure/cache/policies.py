"""Cache policies re-export.

**Feature: test-coverage-80-percent-v2**
**Validates: Requirements 2.1, 2.2**

Re-exports cache policies from core submodule for backward compatibility.
"""

from infrastructure.cache.core.policies import CacheConfig, CacheEntry

__all__ = [
    "CacheConfig",
    "CacheEntry",
]
