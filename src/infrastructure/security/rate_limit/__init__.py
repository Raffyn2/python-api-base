"""Rate limiting implementations with sliding window algorithm.

Provides rate limiting components:
- SlidingWindowRateLimiter: Production-ready sliding window rate limiter
- InMemoryRateLimiter: Simple wrapper for testing
- RateLimitResult: Result of rate limit check with metadata
- SlidingWindowConfig: Configuration for rate limits

Example:
    >>> from infrastructure.security.rate_limit import (
    ...     SlidingWindowRateLimiter,
    ...     parse_rate_limit,
    ... )
    >>> config = parse_rate_limit("100/minute")
    >>> limiter = SlidingWindowRateLimiter(config)
    >>> result = await limiter.is_allowed("user:123")
    >>> if not result.allowed:
    ...     print(f"Rate limited. Retry after {result.retry_after}s")
"""

from infrastructure.security.rate_limit.limiter import (
    InMemoryRateLimiter,
    check_sliding_rate_limit,
    get_client_ip,
    get_sliding_limiter,
    rate_limit_exceeded_handler,
    sliding_rate_limit_response,
)
from infrastructure.security.rate_limit.sliding_window import (
    RateLimitConfigError,
    RateLimitResult,
    SlidingWindowConfig,
    SlidingWindowRateLimiter,
    WindowState,
    parse_rate_limit,
)

__all__ = [
    "InMemoryRateLimiter",
    "RateLimitConfigError",
    "RateLimitResult",
    "SlidingWindowConfig",
    "SlidingWindowRateLimiter",
    "WindowState",
    "check_sliding_rate_limit",
    "get_client_ip",
    "get_sliding_limiter",
    "parse_rate_limit",
    "rate_limit_exceeded_handler",
    "sliding_rate_limit_response",
]
