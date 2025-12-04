"""Generic rate limiting infrastructure with PEP 695 type parameters.

**Feature: enterprise-generics-2025**
**Requirement: R5 - Generic Rate Limiter**

Exports:
    - RateLimiter[TClient]: Generic rate limiter
    - RateLimitResult[TClient]: Typed result
    - RateLimitConfig: Configuration
    - SlidingWindowLimiter: Redis-backed implementation
    - RateLimitMiddleware: FastAPI middleware
"""

from infrastructure.ratelimit.config import RateLimit, RateLimitConfig
from infrastructure.ratelimit.limiter import (
    InMemoryRateLimiter,
    RateLimiter,
    RateLimitResult,
    SlidingWindowLimiter,
)
from infrastructure.ratelimit.middleware import (
    APIKeyExtractor,
    IPClientExtractor,
    RateLimitMiddleware,
    UserIdExtractor,
    rate_limit,
)

__all__ = [
    # Config
    "RateLimitConfig",
    "RateLimit",
    # Core
    "RateLimiter",
    "RateLimitResult",
    "SlidingWindowLimiter",
    "InMemoryRateLimiter",
    # Middleware
    "RateLimitMiddleware",
    "IPClientExtractor",
    "UserIdExtractor",
    "APIKeyExtractor",
    "rate_limit",
]
