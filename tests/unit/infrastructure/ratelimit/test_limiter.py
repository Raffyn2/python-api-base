"""Unit tests for rate limiter implementations.

Tests RateLimitResult, InMemoryRateLimiter, and SlidingWindowLimiter.
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.ratelimit.config import RateLimit, RateLimitConfig
from infrastructure.ratelimit.limiter import (
    InMemoryRateLimiter,
    RateLimitResult,
    SlidingWindowLimiter,
)


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_allowed_result(self) -> None:
        """Test allowed result creation."""
        result: RateLimitResult[str] = RateLimitResult(
            client="user-123",
            is_allowed=True,
            remaining=99,
            limit=100,
            reset_at=datetime.now(UTC),
        )
        assert result.client == "user-123"
        assert result.is_allowed is True
        assert result.remaining == 99
        assert result.limit == 100
        assert result.retry_after is None

    def test_denied_result(self) -> None:
        """Test denied result with retry_after."""
        result: RateLimitResult[str] = RateLimitResult(
            client="user-456",
            is_allowed=False,
            remaining=0,
            limit=100,
            reset_at=datetime.now(UTC),
            retry_after=timedelta(seconds=30),
        )
        assert result.is_allowed is False
        assert result.remaining == 0
        assert result.retry_after == timedelta(seconds=30)

    def test_headers_property(self) -> None:
        """Test headers property."""
        reset_time = datetime.now(UTC)
        result: RateLimitResult[str] = RateLimitResult(
            client="user-1",
            is_allowed=True,
            remaining=50,
            limit=100,
            reset_at=reset_time,
        )
        headers = result.headers
        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "50"
        assert "X-RateLimit-Reset" in headers

    def test_headers_with_retry_after(self) -> None:
        """Test headers include Retry-After when rate limited."""
        result: RateLimitResult[str] = RateLimitResult(
            client="user-1",
            is_allowed=False,
            remaining=0,
            limit=100,
            reset_at=datetime.now(UTC),
            retry_after=timedelta(seconds=60),
        )
        headers = result.headers
        assert headers["Retry-After"] == "60"

    def test_headers_remaining_not_negative(self) -> None:
        """Test remaining in headers is never negative."""
        result: RateLimitResult[str] = RateLimitResult(
            client="user-1",
            is_allowed=False,
            remaining=-5,
            limit=100,
            reset_at=datetime.now(UTC),
        )
        headers = result.headers
        assert headers["X-RateLimit-Remaining"] == "0"

    def test_frozen(self) -> None:
        """Test result is immutable."""
        result: RateLimitResult[str] = RateLimitResult(
            client="user-1",
            is_allowed=True,
            remaining=50,
            limit=100,
            reset_at=datetime.now(UTC),
        )
        with pytest.raises(AttributeError):
            result.is_allowed = False  # type: ignore[misc]


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    @pytest.fixture
    def config(self) -> RateLimitConfig:
        """Create test configuration."""
        return RateLimitConfig()

    @pytest.fixture
    def limiter(self, config: RateLimitConfig) -> InMemoryRateLimiter[str]:
        """Create test limiter."""
        return InMemoryRateLimiter(config)

    @pytest.mark.asyncio
    async def test_first_request_allowed(
        self, limiter: InMemoryRateLimiter[str]
    ) -> None:
        """Test first request is allowed."""
        limit = RateLimit(requests=10, window=timedelta(minutes=1))
        result = await limiter.check("user-1", limit)
        assert result.is_allowed is True
        assert result.remaining == 9

    @pytest.mark.asyncio
    async def test_requests_decrement_remaining(
        self, limiter: InMemoryRateLimiter[str]
    ) -> None:
        """Test remaining decrements with each request."""
        limit = RateLimit(requests=5, window=timedelta(minutes=1))

        result1 = await limiter.check("user-1", limit)
        assert result1.remaining == 4

        result2 = await limiter.check("user-1", limit)
        assert result2.remaining == 3

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(
        self, limiter: InMemoryRateLimiter[str]
    ) -> None:
        """Test rate limit is enforced."""
        limit = RateLimit(requests=3, window=timedelta(minutes=1))

        # Use up all requests
        for _ in range(3):
            result = await limiter.check("user-1", limit)
            assert result.is_allowed is True

        # Next request should be denied
        result = await limiter.check("user-1", limit)
        assert result.is_allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None

    @pytest.mark.asyncio
    async def test_different_clients_independent(
        self, limiter: InMemoryRateLimiter[str]
    ) -> None:
        """Test different clients have independent limits."""
        limit = RateLimit(requests=2, window=timedelta(minutes=1))

        # User 1 uses their limit
        await limiter.check("user-1", limit)
        await limiter.check("user-1", limit)
        result1 = await limiter.check("user-1", limit)
        assert result1.is_allowed is False

        # User 2 should still have their limit
        result2 = await limiter.check("user-2", limit)
        assert result2.is_allowed is True

    @pytest.mark.asyncio
    async def test_different_endpoints_independent(
        self, limiter: InMemoryRateLimiter[str]
    ) -> None:
        """Test different endpoints have independent limits."""
        limit = RateLimit(requests=2, window=timedelta(minutes=1))

        # Use up limit on endpoint A
        await limiter.check("user-1", limit, "endpoint-a")
        await limiter.check("user-1", limit, "endpoint-a")
        result_a = await limiter.check("user-1", limit, "endpoint-a")
        assert result_a.is_allowed is False

        # Endpoint B should still have limit
        result_b = await limiter.check("user-1", limit, "endpoint-b")
        assert result_b.is_allowed is True

    @pytest.mark.asyncio
    async def test_reset_clears_limit(
        self, limiter: InMemoryRateLimiter[str]
    ) -> None:
        """Test reset clears rate limit."""
        limit = RateLimit(requests=2, window=timedelta(minutes=1))

        # Use up limit
        await limiter.check("user-1", limit)
        await limiter.check("user-1", limit)
        result = await limiter.check("user-1", limit)
        assert result.is_allowed is False

        # Reset
        reset_result = await limiter.reset("user-1")
        assert reset_result is True

        # Should be allowed again
        result = await limiter.check("user-1", limit)
        assert result.is_allowed is True

    @pytest.mark.asyncio
    async def test_reset_nonexistent_returns_false(
        self, limiter: InMemoryRateLimiter[str]
    ) -> None:
        """Test reset returns False for nonexistent client."""
        result = await limiter.reset("nonexistent-user")
        assert result is False


class TestSlidingWindowLimiter:
    """Tests for SlidingWindowLimiter (fallback mode)."""

    @pytest.fixture
    def config(self) -> RateLimitConfig:
        """Create test configuration."""
        return RateLimitConfig()

    @pytest.fixture
    def limiter(self, config: RateLimitConfig) -> SlidingWindowLimiter[str]:
        """Create test limiter without Redis (uses fallback)."""
        return SlidingWindowLimiter(config, redis_client=None)

    @pytest.mark.asyncio
    async def test_fallback_to_inmemory(
        self, limiter: SlidingWindowLimiter[str]
    ) -> None:
        """Test falls back to in-memory when no Redis."""
        limit = RateLimit(requests=10, window=timedelta(minutes=1))
        result = await limiter.check("user-1", limit)
        assert result.is_allowed is True

    @pytest.mark.asyncio
    async def test_fallback_enforces_limit(
        self, limiter: SlidingWindowLimiter[str]
    ) -> None:
        """Test fallback enforces rate limit."""
        limit = RateLimit(requests=2, window=timedelta(minutes=1))

        await limiter.check("user-1", limit)
        await limiter.check("user-1", limit)
        result = await limiter.check("user-1", limit)
        assert result.is_allowed is False

    @pytest.mark.asyncio
    async def test_fallback_reset(
        self, limiter: SlidingWindowLimiter[str]
    ) -> None:
        """Test fallback reset works."""
        limit = RateLimit(requests=1, window=timedelta(minutes=1))

        await limiter.check("user-1", limit)
        await limiter.reset("user-1")

        result = await limiter.check("user-1", limit)
        assert result.is_allowed is True
