"""JWT algorithm provider implementations.

Re-exports all provider classes for backward compatibility.
Implementation split into focused modules for one-class-per-file compliance.

**Feature: api-base-score-100, api-best-practices-review-2025**
**Validates: Requirements 1.1, 1.2, 1.4, 20.1, 20.2**
**Refactored: Split into focused modules for one-class-per-file compliance**
"""

# Re-export all classes for backward compatibility
from infrastructure.auth.jwt.es256_provider import ES256Provider
from infrastructure.auth.jwt.hs256_provider import HS256Provider
from infrastructure.auth.jwt.rs256_provider import RS256Provider

__all__ = [
    "ES256Provider",
    "HS256Provider",
    "RS256Provider",
]
