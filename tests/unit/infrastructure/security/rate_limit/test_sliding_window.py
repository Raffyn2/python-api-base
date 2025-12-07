"""Unit tests for SlidingWindowRateLimiter.

Tests sliding window algorithm, configuration, and rate limiting.
"""

import pytest

from infrastructure.security.rate_limit.sliding_window import (
    RateLimitConfigError,
    RateLimitResult,
    SlidingWindowConfig,
    SlidingWindowRateLimiter,
    WindowState,
    parse_rate_limit,
)


class TestSlidingWindowConfig:
    """Tests for SlidingWindowConfig."""

    def test_valid_config(self) -> None:
        """Test valid configuration creation."""
        config = SlidingWindowConfig(
            requests_per_window=100,
            window_size_seconds=60,
        )

        assert config.requests_per_window == 100
        assert config.window_size_seconds == 60

    def test_invalid_requests_zero(self) -> None:
        """Test validation rejects zero requests."""
        with pytest.raises(RateLimitConfigError, match="must be positive"):
            SlidingWindowConfig(requests_per_window=0, window_size_seconds=60)

    def test_invalid_requests_negative(self) -> None:
        """Test validation rejects negative requests."""
        with pytest.raises(RateLimitConfigError, match="must be positive"):
            SlidingWindowConfig(requests_per_window=-1, window_size_seconds=60)

    def test_invalid_window_zero(self) -> None:
        """Test validation rejects zero window size."""
        with pytest.raises(RateLimitConfigError, match="must be positive"):
            SlidingWindowConfig(requests_per_window=100, window_size_seconds=0)

    def test_invalid_window_negative(self) -> None:
        """Test validation rejects negative window size."""
        with pytest.raises(RateLimitConfigError, match="must be positive"):
            SlidingWindowConfig(requests_per_window=100, window_size_seconds=-1)


class TestSlidingWindowConfigFromString:
    """Tests for SlidingWindowConfig.from_string."""

    def test_parse_per_second(self) -> None:
        """Test parsing per second rate limit."""
        config = SlidingWindowConfig.from_string("10/second")

        assert config.requests_per_window == 10
        assert config.window_size_seconds == 1

    def test_parse_per_seconds(self) -> None:
        """Test parsing per seconds (plural) rate limit."""
        config = SlidingWindowConfig.from_string("10/seconds")

        assert config.requests_per_window == 10
        assert config.window_size_seconds == 1

    def test_parse_per_minute(self) -> None:
        """Test parsing per minute rate limit."""
        config = SlidingWindowConfig.from_string("100/minute")

        assert config.requests_per_window == 100
        assert config.window_size_seconds == 60

    def test_parse_per_minutes(self) -> None:
        """Test parsing per minutes (plural) rate limit."""
        config = SlidingWindowConfig.from_string("100/minutes")

        assert config.requests_per_window == 100
        assert config.window_size_seconds == 60

    def test_parse_per_hour(self) -> None:
        """Test parsing per hour rate limit."""
        config = SlidingWindowConfig.from_string("1000/hour")

        assert config.requests_per_window == 1000
        assert config.window_size_seconds == 3600

    def test_parse_per_day(self) -> None:
        """Test parsing per day rate limit."""
        config = SlidingWindowConfig.from_string("10000/day")

        assert config.requests_per_window == 10000
        assert config.window_size_seconds == 86400

    def test_parse_with_whitespace(self) -> None:
        """Test parsing with leading/trailing whitespace."""
        config = SlidingWindowConfig.from_string("  100/minute  ")

        assert config.requests_per_window == 100

    def test_invalid_format_no_slash(self) -> None:
        """Test invalid format without slash."""
        with pytest.raises(RateLimitConfigError, match="Invalid rate limit format"):
            SlidingWindowConfig.from_string("100minute")

    def test_invalid_format_empty(self) -> None:
        """Test invalid empty format."""
        with pytest.raises(RateLimitConfigError, match="Invalid rate limit format"):
            SlidingWindowConfig.from_string("")

    def test_invalid_unit(self) -> None:
        """Test invalid time unit."""
        with pytest.raises(RateLimitConfigError, match="Invalid time unit"):
            SlidingWindowConfig.from_string("100/week")


class TestWindowState:
    """Tests for WindowState dataclass."""

    def test_creation(self) -> None:
        """Test WindowState creation."""
        state = WindowState(window_start=1000.0)

        assert state.window_start == 1000.0
        assert state.current_count == 0
        assert state.previous_count == 0

    def test_creation_with_counts(self) -> None:
        """Test WindowState creation with counts."""
        state = WindowState(
            window_start=1000.0,
            current_count=50,
            previous_count=30,
        )

        assert state.current_count == 50
        assert state.previous_count == 30


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_allowed_result(self) -> None:
        """Test allowed result."""
        result = RateLimitResult(
            allowed=True,
            remaining=99,
            retry_after=0,
            weighted_count=1.0,
        )

        assert result.allowed is True
        assert result.remaining == 99
        assert result.retry_after == 0

    def test_blocked_result(self) -> None:
        """Test blocked result."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            retry_after=30,
            weighted_count=100.0,
        )

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    @pytest.fixture
    def limiter(self) -> SlidingWindowRateLimiter:
        """Create limiter with small limit for testing."""
        config = SlidingWindowConfig(
            requests_per_window=5,
            window_size_seconds=60,
        )
        return SlidingWindowRateLimiter(config)

    @pytest.mark.asyncio
    async def test_allows_under_limit(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Test requests under limit are allowed."""
        result = await limiter.is_allowed("client1")

        assert result.allowed is True
        assert result.remaining >= 0

    @pytest.mark.asyncio
    async def test_allows_up_to_limit(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Test requests up to limit are allowed."""
        for i in range(5):
            result = await limiter.is_allowed("client1")
            assert result.allowed is True, f"Request {i+1} should be allowed"

    @pytest.mark.asyncio
    async def test_blocks_over_limit(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Test requests over limit are blocked."""
        for _ in range(5):
            await limiter.is_allowed("client1")

        result = await limiter.is_allowed("client1")

        assert result.allowed is False
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_separate_clients(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Test clients are tracked separately."""
        for _ in range(5):
            await limiter.is_allowed("client1")

        result = await limiter.is_allowed("client2")

        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_get_state(self, limiter: SlidingWindowRateLimiter) -> None:
        """Test get_state returns window state."""
        await limiter.is_allowed("client1")

        state = await limiter.get_state("client1")

        assert state is not None
        assert state.current_count == 1

    @pytest.mark.asyncio
    async def test_get_state_not_found(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Test get_state returns None for unknown client."""
        state = await limiter.get_state("unknown")

        assert state is None

    @pytest.mark.asyncio
    async def test_reset(self, limiter: SlidingWindowRateLimiter) -> None:
        """Test reset clears client state."""
        await limiter.is_allowed("client1")

        result = await limiter.reset("client1")

        assert result is True
        state = await limiter.get_state("client1")
        assert state is None

    @pytest.mark.asyncio
    async def test_reset_not_found(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        """Test reset returns False for unknown client."""
        result = await limiter.reset("unknown")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_all(self, limiter: SlidingWindowRateLimiter) -> None:
        """Test clear_all removes all states."""
        await limiter.is_allowed("client1")
        await limiter.is_allowed("client2")

        count = await limiter.clear_all()

        assert count == 2
        assert await limiter.get_state("client1") is None
        assert await limiter.get_state("client2") is None


class TestParseRateLimit:
    """Tests for parse_rate_limit function."""

    def test_parse_rate_limit(self) -> None:
        """Test parse_rate_limit function."""
        config = parse_rate_limit("100/minute")

        assert config.requests_per_window == 100
        assert config.window_size_seconds == 60

    def test_parse_rate_limit_invalid(self) -> None:
        """Test parse_rate_limit with invalid format."""
        with pytest.raises(RateLimitConfigError):
            parse_rate_limit("invalid")


class TestRateLimitConfigError:
    """Tests for RateLimitConfigError."""

    def test_error_message(self) -> None:
        """Test error message is stored."""
        error = RateLimitConfigError("test message")

        assert error.message == "test message"
        assert "test message" in str(error)
