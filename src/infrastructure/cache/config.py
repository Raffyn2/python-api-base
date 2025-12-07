"""Cache config re-export.

**Feature: test-coverage-80-percent-v2**
**Validates: Requirements 2.1, 2.2**

Re-exports cache config from core submodule for backward compatibility.
"""

from infrastructure.cache.core.config import CacheConfig

__all__ = [
    "CacheConfig",
]
