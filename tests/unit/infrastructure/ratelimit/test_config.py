"""Tests for rate limiter configuration.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from datetime import timedelta

import pytest

from infrastructure.ratelimit.config import (
    API_RATE_LIMITS,
    RateLimit,
    RateLimitAlgorithm,
    RateLimitConfig,
    get_rate_limit,
)


class TestRateLimitAlgorithm:
    """Tests for RateLimitAlgorithm enum."""

    def test_sliding_window_value(self) -> None:
        """Test sliding window algorithm value."""
        assert RateLimitAlgorithm.SLIDING_WINDOW.value == "sliding_window"

    def test_fixed_window_value(self) -> None:
        """Test fixed window algorithm value."""
        assert RateLimitAlgorithm.FIXED_WINDOW.value == "fixed_window"

    def test_token_bucket_value(self) -> None:
        """Test token bucket algorithm value."""
        assert RateLimitAlgorithm.TOKEN_BUCKET.value == "token_bucket"

    def test_leaky_bucket_value(self) -> None:
        """Test leaky bucket algorithm value."""
        assert RateLimitAlgorithm.LEAKY_BUCKET.value == "leaky_bucket"


class TestRateLimit:
    """Tests for RateLimit dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic rate limit creation."""
        limit = RateLimit(requests=100, window=timedelta(minutes=1))
        assert limit.requests == 100
        assert limit.window == timedelta(minutes=1)
        assert limit.burst == 0

    def test_with_burst(self) -> None:
        """Test rate limit with burst allowance."""
        limit = RateLimit(requests=100, window=timedelta(minutes=1), burst=20)
        assert limit.burst == 20

    def test_window_seconds_property(self) -> None:
        """Test window_seconds property."""
        limit = RateLimit(requests=100, window=timedelta(minutes=2))
        assert limit.window_seconds == 120.0

    def test_window_seconds_with_hours(self) -> None:
        """Test window_seconds with hours."""
        limit = RateLimit(requests=1000, window=timedelta(hours=1))
        assert limit.window_seconds == 3600.0

    def test_zero_requests_raises(self) -> None:
        """Test that zero requests raises ValueError."""
        with pytest.raises(ValueError, match="requests must be positive"):
            RateLimit(requests=0, window=timedelta(minutes=1))

    def test_negative_requests_raises(self) -> None:
        """Test that negative requests raises ValueError."""
        with pytest.raises(ValueError, match="requests must be positive"):
            RateLimit(requests=-10, window=timedelta(minutes=1))

    def test_zero_window_raises(self) -> None:
        """Test that zero window raises ValueError."""
        with pytest.raises(ValueError, match="window must be positive"):
            RateLimit(requests=100, window=timedelta(seconds=0))

    def test_negative_burst_raises(self) -> None:
        """Test that negative burst raises ValueError."""
        with pytest.raises(ValueError, match="burst cannot be negative"):
            RateLimit(requests=100, window=timedelta(minutes=1), burst=-5)

    def test_frozen_dataclass(self) -> None:
        """Test that RateLimit is immutable."""
        limit = RateLimit(requests=100, window=timedelta(minutes=1))
        with pytest.raises(AttributeError):
            limit.requests = 200


class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.key_prefix == "ratelimit:"
        assert config.enabled is True
        assert config.default_limit.requests == 100

    def test_custom_algorithm(self) -> None:
        """Test custom algorithm configuration."""
        config = RateLimitConfig(algorithm=RateLimitAlgorithm.TOKEN_BUCKET)
        assert config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET

    def test_custom_redis_url(self) -> None:
        """Test custom Redis URL configuration."""
        config = RateLimitConfig(redis_url="redis://redis.example.com:6380/1")
        assert config.redis_url == "redis://redis.example.com:6380/1"

    def test_custom_key_prefix(self) -> None:
        """Test custom key prefix configuration."""
        config = RateLimitConfig(key_prefix="myapp:ratelimit:")
        assert config.key_prefix == "myapp:ratelimit:"

    def test_custom_default_limit(self) -> None:
        """Test custom default limit configuration."""
        custom_limit = RateLimit(requests=50, window=timedelta(seconds=30))
        config = RateLimitConfig(default_limit=custom_limit)
        assert config.default_limit.requests == 50
        assert config.default_limit.window == timedelta(seconds=30)

    def test_disabled_config(self) -> None:
        """Test disabled rate limiting configuration."""
        config = RateLimitConfig(enabled=False)
        assert config.enabled is False

    def test_get_redis_key_default_endpoint(self) -> None:
        """Test get_redis_key with default endpoint."""
        config = RateLimitConfig()
        key = config.get_redis_key("client-123")
        assert key == "ratelimit:default:client-123"

    def test_get_redis_key_custom_endpoint(self) -> None:
        """Test get_redis_key with custom endpoint."""
        config = RateLimitConfig()
        key = config.get_redis_key("client-456", endpoint="api/users")
        assert key == "ratelimit:api/users:client-456"

    def test_get_redis_key_custom_prefix(self) -> None:
        """Test get_redis_key with custom prefix."""
        config = RateLimitConfig(key_prefix="app:")
        key = config.get_redis_key("client-789", endpoint="search")
        assert key == "app:search:client-789"


class TestAPIRateLimits:
    """Tests for API_RATE_LIMITS preset."""

    def test_default_limit_exists(self) -> None:
        """Test that default limit exists."""
        assert "default" in API_RATE_LIMITS
        assert API_RATE_LIMITS["default"].requests == 100

    def test_auth_limit_exists(self) -> None:
        """Test that auth limit exists."""
        assert "auth" in API_RATE_LIMITS
        assert API_RATE_LIMITS["auth"].requests == 10

    def test_search_limit_exists(self) -> None:
        """Test that search limit exists."""
        assert "search" in API_RATE_LIMITS
        assert API_RATE_LIMITS["search"].requests == 30

    def test_upload_limit_exists(self) -> None:
        """Test that upload limit exists."""
        assert "upload" in API_RATE_LIMITS
        assert API_RATE_LIMITS["upload"].requests == 5

    def test_webhook_limit_exists(self) -> None:
        """Test that webhook limit exists."""
        assert "webhook" in API_RATE_LIMITS
        assert API_RATE_LIMITS["webhook"].requests == 1000


class TestGetRateLimit:
    """Tests for get_rate_limit function."""

    def test_get_known_endpoint(self) -> None:
        """Test getting rate limit for known endpoint."""
        limit = get_rate_limit("auth")
        assert limit.requests == 10

    def test_get_unknown_endpoint_returns_default(self) -> None:
        """Test that unknown endpoint returns default limit."""
        limit = get_rate_limit("unknown-endpoint")
        assert limit.requests == 100
        assert limit == API_RATE_LIMITS["default"]

    def test_get_search_endpoint(self) -> None:
        """Test getting rate limit for search endpoint."""
        limit = get_rate_limit("search")
        assert limit.requests == 30
