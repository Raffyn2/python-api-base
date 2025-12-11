"""Unit tests for rate limiter implementations.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements R5.1, R5.2, R5.3, R5.4, R5.6**
"""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from infrastructure.ratelimit.config import RateLimit, RateLimitConfig
from infrastructure.ratelimit.limiter import (
    InMemoryRateLimiter,
    RateLimitResult,
    SlidingWindowLimiter,
)


class TestRateLimitResult:
    """Tests for RateLimitResult."""

    def test_headers_without_retry(self) -> None:
        """Test headers without retry_after."""
        from datetime import UTC, datetime

        result = RateLimitResult(
            client="user-1",
            is_allowed=True,
            remaining=99,
            limit=100,
            reset_at=datetime.now(UTC),
        )

        headers = result.headers

        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "99"
        assert "X-RateLimit-Reset" in headers
        assert "Retry-After" not in headers

    def test_headers_with_retry(self) -> None:
        """Test headers with retry_after."""
        from datetime import UTC, datetime

        result = RateLimitResult(
            client="user-1",
            is_allowed=False,
            remaining=0,
            limit=100,
            reset_at=datetime.now(UTC),
            retry_after=timedelta(seconds=30),
        )

        headers = result.headers

        assert headers["Retry-After"] == "30"

    def test_remaining_clamped_to_zero(self) -> None:
        """Test remaining is clamped to 0 in headers."""
        from datetime import UTC, datetime

        result = RateLimitResult(
            client="user-1",
            is_allowed=False,
            remaining=-5,
            limit=100,
            reset_at=datetime.now(UTC),
        )

        headers = result.headers

        assert headers["X-RateLimit-Remaining"] == "0"


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    @pytest.fixture()
    def config(self) -> RateLimitConfig:
        """Create rate limit config."""
        return RateLimitConfig()

    @pytest.fixture()
    def limiter(self, config: RateLimitConfig) -> InMemoryRateLimiter[str]:
        """Create in-memory rate limiter."""
        return InMemoryRateLimiter[str](config)

    @pytest.fixture()
    def limit(self) -> RateLimit:
        """Create rate limit."""
        return RateLimit(requests=5, window=timedelta(seconds=60))

    @pytest.mark.asyncio
    async def test_allows_under_limit(self, limiter: InMemoryRateLimiter[str], limit: RateLimit) -> None:
        """Test requests under limit are allowed."""
        result = await limiter.check("user-1", limit)

        assert result.is_allowed is True
        assert result.remaining == 4
        assert result.client == "user-1"

    @pytest.mark.asyncio
    async def test_denies_over_limit(self, limiter: InMemoryRateLimiter[str], limit: RateLimit) -> None:
        """Test requests over limit are denied."""
        # Exhaust the limit
        for _ in range(5):
            await limiter.check("user-1", limit)

        result = await limiter.check("user-1", limit)

        assert result.is_allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None

    @pytest.mark.asyncio
    async def test_separate_clients(self, limiter: InMemoryRateLimiter[str], limit: RateLimit) -> None:
        """Test different clients have separate limits."""
        # Exhaust user-1's limit
        for _ in range(5):
            await limiter.check("user-1", limit)

        # user-2 should still be allowed
        result = await limiter.check("user-2", limit)

        assert result.is_allowed is True

    @pytest.mark.asyncio
    async def test_separate_endpoints(self, limiter: InMemoryRateLimiter[str], limit: RateLimit) -> None:
        """Test different endpoints have separate limits."""
        # Exhaust limit for endpoint-1
        for _ in range(5):
            await limiter.check("user-1", limit, endpoint="endpoint-1")

        # Same user on endpoint-2 should be allowed
        result = await limiter.check("user-1", limit, endpoint="endpoint-2")

        assert result.is_allowed is True

    @pytest.mark.asyncio
    async def test_reset_clears_limit(self, limiter: InMemoryRateLimiter[str], limit: RateLimit) -> None:
        """Test reset clears rate limit."""
        # Exhaust the limit
        for _ in range(5):
            await limiter.check("user-1", limit)

        # Reset
        result = await limiter.reset("user-1")
        assert result is True

        # Should be allowed again
        check_result = await limiter.check("user-1", limit)
        assert check_result.is_allowed is True

    @pytest.mark.asyncio
    async def test_reset_nonexistent_returns_false(self, limiter: InMemoryRateLimiter[str]) -> None:
        """Test reset for nonexistent client returns False."""
        result = await limiter.reset("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_configure_limits(self, limiter: InMemoryRateLimiter[str]) -> None:
        """Test configuring per-endpoint limits."""
        custom_limit = RateLimit(requests=10, window=timedelta(seconds=30))
        limiter.configure({"custom": custom_limit})

        retrieved = limiter.get_limit("custom")

        assert retrieved.requests == 10

    @pytest.mark.asyncio
    async def test_get_default_limit(self, limiter: InMemoryRateLimiter[str], config: RateLimitConfig) -> None:
        """Test getting default limit for unknown endpoint."""
        retrieved = limiter.get_limit("unknown")

        assert retrieved == config.default_limit


class TestSlidingWindowLimiter:
    """Tests for SlidingWindowLimiter."""

    @pytest.fixture()
    def config(self) -> RateLimitConfig:
        """Create rate limit config."""
        return RateLimitConfig()

    @pytest.fixture()
    def limit(self) -> RateLimit:
        """Create rate limit."""
        return RateLimit(requests=5, window=timedelta(seconds=60))

    @pytest.mark.asyncio
    async def test_fallback_without_redis(self, config: RateLimitConfig, limit: RateLimit) -> None:
        """Test fallback to in-memory without Redis."""
        limiter = SlidingWindowLimiter[str](config, redis_client=None)

        result = await limiter.check("user-1", limit)

        assert result.is_allowed is True

    @pytest.mark.asyncio
    async def test_fallback_on_redis_error(self, config: RateLimitConfig, limit: RateLimit) -> None:
        """Test fallback to in-memory on Redis error."""
        mock_redis = AsyncMock()
        mock_redis.pipeline.side_effect = Exception("Redis error")

        limiter = SlidingWindowLimiter[str](config, redis_client=mock_redis)

        result = await limiter.check("user-1", limit)

        assert result.is_allowed is True

    @pytest.mark.asyncio
    async def test_reset_fallback_without_redis(self, config: RateLimitConfig, limit: RateLimit) -> None:
        """Test reset fallback without Redis."""
        limiter = SlidingWindowLimiter[str](config, redis_client=None)

        # First make a request
        await limiter.check("user-1", limit)

        # Reset should work via fallback
        result = await limiter.reset("user-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_reset_fallback_on_redis_error(self, config: RateLimitConfig) -> None:
        """Test reset fallback on Redis error."""
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = Exception("Redis error")

        limiter = SlidingWindowLimiter[str](config, redis_client=mock_redis)

        result = await limiter.reset("user-1")
        assert result is False


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = RateLimitConfig()

        assert config.enabled is True
        assert config.key_prefix == "ratelimit:"

    def test_get_redis_key(self) -> None:
        """Test Redis key generation."""
        config = RateLimitConfig(key_prefix="test:")

        key = config.get_redis_key("user-123", "api")

        assert key == "test:api:user-123"

    def test_get_redis_key_default_endpoint(self) -> None:
        """Test Redis key with default endpoint."""
        config = RateLimitConfig()

        key = config.get_redis_key("user-123")

        assert "default" in key


class TestRateLimit:
    """Tests for RateLimit dataclass."""

    def test_valid_rate_limit(self) -> None:
        """Test valid rate limit creation."""
        limit = RateLimit(requests=100, window=timedelta(minutes=1))

        assert limit.requests == 100
        assert limit.window_seconds == 60.0

    def test_invalid_requests_raises(self) -> None:
        """Test invalid requests raises ValueError."""
        with pytest.raises(ValueError, match="requests must be positive"):
            RateLimit(requests=0, window=timedelta(minutes=1))

    def test_invalid_window_raises(self) -> None:
        """Test invalid window raises ValueError."""
        with pytest.raises(ValueError, match="window must be positive"):
            RateLimit(requests=100, window=timedelta(seconds=0))

    def test_negative_burst_raises(self) -> None:
        """Test negative burst raises ValueError."""
        with pytest.raises(ValueError, match="burst cannot be negative"):
            RateLimit(requests=100, window=timedelta(minutes=1), burst=-1)

    def test_burst_default(self) -> None:
        """Test burst defaults to 0."""
        limit = RateLimit(requests=100, window=timedelta(minutes=1))
        assert limit.burst == 0
