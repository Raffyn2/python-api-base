"""Unit tests for rate limiter.

Tests IP validation and InMemoryRateLimiter.
"""

import pytest

from infrastructure.security.rate_limit.limiter import (
    InMemoryRateLimiter,
    _is_valid_ip,
)


class TestIsValidIp:
    """Tests for _is_valid_ip function."""

    def test_valid_ipv4(self) -> None:
        """Test valid IPv4 address."""
        assert _is_valid_ip("192.168.1.1") is True

    def test_valid_ipv4_localhost(self) -> None:
        """Test localhost IPv4."""
        assert _is_valid_ip("127.0.0.1") is True

    def test_valid_ipv6(self) -> None:
        """Test valid IPv6 address."""
        assert _is_valid_ip("::1") is True

    def test_valid_ipv6_full(self) -> None:
        """Test full IPv6 address."""
        assert _is_valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True

    def test_empty_string(self) -> None:
        """Test empty string is invalid."""
        assert _is_valid_ip("") is False

    def test_whitespace_only(self) -> None:
        """Test whitespace only is invalid."""
        assert _is_valid_ip("   ") is False

    def test_invalid_format(self) -> None:
        """Test invalid IP format."""
        assert _is_valid_ip("not-an-ip") is False

    def test_invalid_ipv4_out_of_range(self) -> None:
        """Test IPv4 with out of range octet."""
        assert _is_valid_ip("256.1.1.1") is False

    def test_too_long(self) -> None:
        """Test IP exceeding max length."""
        long_ip = "a" * 50
        assert _is_valid_ip(long_ip) is False

    def test_with_whitespace(self) -> None:
        """Test IP with leading/trailing whitespace."""
        assert _is_valid_ip("  192.168.1.1  ") is True


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    @pytest.fixture
    def limiter(self) -> InMemoryRateLimiter:
        """Create limiter with small limit for testing."""
        return InMemoryRateLimiter(limit=3, window_seconds=60)

    @pytest.mark.asyncio
    async def test_allows_under_limit(self, limiter: InMemoryRateLimiter) -> None:
        """Test requests under limit are allowed."""
        result = await limiter.is_allowed("client1")

        assert result is True

    @pytest.mark.asyncio
    async def test_allows_up_to_limit(self, limiter: InMemoryRateLimiter) -> None:
        """Test requests up to limit are allowed."""
        for _ in range(3):
            result = await limiter.is_allowed("client1")
            assert result is True

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self, limiter: InMemoryRateLimiter) -> None:
        """Test requests over limit are blocked."""
        for _ in range(3):
            await limiter.is_allowed("client1")

        result = await limiter.is_allowed("client1")

        assert result is False

    @pytest.mark.asyncio
    async def test_separate_clients(self, limiter: InMemoryRateLimiter) -> None:
        """Test clients are tracked separately."""
        for _ in range(3):
            await limiter.is_allowed("client1")

        # client2 should still be allowed
        result = await limiter.is_allowed("client2")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_remaining_full(self, limiter: InMemoryRateLimiter) -> None:
        """Test get_remaining returns full limit for new client."""
        remaining = await limiter.get_remaining("new_client")

        assert remaining == 3

    @pytest.mark.asyncio
    async def test_get_remaining_after_requests(
        self, limiter: InMemoryRateLimiter
    ) -> None:
        """Test get_remaining decreases after requests."""
        await limiter.is_allowed("client1")
        await limiter.is_allowed("client1")

        remaining = await limiter.get_remaining("client1")

        assert remaining == 1

    @pytest.mark.asyncio
    async def test_get_remaining_at_limit(
        self, limiter: InMemoryRateLimiter
    ) -> None:
        """Test get_remaining returns 0 at limit."""
        for _ in range(3):
            await limiter.is_allowed("client1")

        remaining = await limiter.get_remaining("client1")

        assert remaining == 0

    def test_reset_specific_client(self, limiter: InMemoryRateLimiter) -> None:
        """Test reset for specific client."""
        limiter._requests["client1"] = [1.0, 2.0, 3.0]
        limiter._requests["client2"] = [1.0, 2.0]

        limiter.reset("client1")

        assert "client1" not in limiter._requests
        assert "client2" in limiter._requests

    def test_reset_all_clients(self, limiter: InMemoryRateLimiter) -> None:
        """Test reset for all clients."""
        limiter._requests["client1"] = [1.0, 2.0, 3.0]
        limiter._requests["client2"] = [1.0, 2.0]

        limiter.reset()

        assert len(limiter._requests) == 0

    def test_reset_nonexistent_client(self, limiter: InMemoryRateLimiter) -> None:
        """Test reset for nonexistent client does nothing."""
        limiter.reset("nonexistent")  # Should not raise

    @pytest.mark.asyncio
    async def test_default_values(self) -> None:
        """Test default limit and window values."""
        limiter = InMemoryRateLimiter()

        assert limiter._limit == 100
        assert limiter._window_seconds == 60



class TestGetClientIp:
    """Tests for get_client_ip function."""

    def test_get_client_ip_from_forwarded_header(self) -> None:
        """Test getting IP from X-Forwarded-For header."""
        from unittest.mock import MagicMock

        from infrastructure.security.rate_limit.limiter import get_client_ip

        request = MagicMock()
        request.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}

        ip = get_client_ip(request)

        assert ip == "192.168.1.100"

    def test_get_client_ip_invalid_forwarded(self) -> None:
        """Test fallback when X-Forwarded-For has invalid IP."""
        from unittest.mock import MagicMock, patch

        from infrastructure.security.rate_limit.limiter import get_client_ip

        request = MagicMock()
        request.headers = {"X-Forwarded-For": "invalid-ip"}

        with patch(
            "infrastructure.security.rate_limit.limiter.get_remote_address"
        ) as mock_remote:
            mock_remote.return_value = "127.0.0.1"
            ip = get_client_ip(request)

        assert ip == "127.0.0.1"

    def test_get_client_ip_no_forwarded(self) -> None:
        """Test getting IP when no X-Forwarded-For header."""
        from unittest.mock import MagicMock, patch

        from infrastructure.security.rate_limit.limiter import get_client_ip

        request = MagicMock()
        request.headers = {}

        with patch(
            "infrastructure.security.rate_limit.limiter.get_remote_address"
        ) as mock_remote:
            mock_remote.return_value = "10.0.0.1"
            ip = get_client_ip(request)

        assert ip == "10.0.0.1"


class TestGetRateLimit:
    """Tests for get_rate_limit function."""

    def test_get_rate_limit_returns_string(self) -> None:
        """Test get_rate_limit returns rate limit string."""
        from unittest.mock import MagicMock, patch

        from infrastructure.security.rate_limit.limiter import get_rate_limit

        mock_settings = MagicMock()
        mock_settings.security.rate_limit = "100/minute"

        with patch(
            "infrastructure.security.rate_limit.limiter.get_settings"
        ) as mock_get:
            mock_get.return_value = mock_settings
            result = get_rate_limit()

        assert result == "100/minute"


class TestSlidingRateLimitResponse:
    """Tests for sliding_rate_limit_response function."""

    @pytest.mark.asyncio
    async def test_creates_429_response(self) -> None:
        """Test creates 429 response with correct headers."""
        from unittest.mock import MagicMock

        from infrastructure.security.rate_limit.limiter import (
            sliding_rate_limit_response,
        )
        from infrastructure.security.rate_limit.sliding_window import RateLimitResult

        request = MagicMock()
        request.url = "http://example.com/api/test"

        result = RateLimitResult(
            allowed=False,
            remaining=0,
            retry_after=30,
            weighted_count=100.0,
        )

        response = await sliding_rate_limit_response(request, result)

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "30"
        assert response.headers["X-RateLimit-Remaining"] == "0"

    @pytest.mark.asyncio
    async def test_response_contains_problem_detail(self) -> None:
        """Test response body contains RFC 7807 problem detail."""
        import json
        from unittest.mock import MagicMock

        from infrastructure.security.rate_limit.limiter import (
            sliding_rate_limit_response,
        )
        from infrastructure.security.rate_limit.sliding_window import RateLimitResult

        request = MagicMock()
        request.url = "http://example.com/api/test"

        result = RateLimitResult(
            allowed=False,
            remaining=0,
            retry_after=60,
            weighted_count=100.0,
        )

        response = await sliding_rate_limit_response(request, result)
        body = json.loads(response.body.decode())

        assert body["status"] == 429
        assert body["title"] == "Rate Limit Exceeded"
        assert "RATE_LIMIT_EXCEEDED" in body["type"]


class TestRateLimitExceededHandler:
    """Tests for rate_limit_exceeded_handler function."""

    @pytest.mark.asyncio
    async def test_handler_returns_429(self) -> None:
        """Test handler returns 429 status code."""
        from unittest.mock import MagicMock, patch

        from infrastructure.security.rate_limit.limiter import (
            rate_limit_exceeded_handler,
        )

        request = MagicMock()
        request.url = "http://example.com/api/test"
        request.headers = {}

        # Create mock exception with detail attribute
        exc = MagicMock()
        exc.detail = "Rate limit exceeded"

        with patch(
            "infrastructure.security.rate_limit.limiter.get_sliding_limiter"
        ) as mock_limiter:
            mock_limiter.return_value.get_state.return_value = None
            with patch(
                "infrastructure.security.rate_limit.limiter.get_remote_address"
            ) as mock_remote:
                mock_remote.return_value = "127.0.0.1"
                response = await rate_limit_exceeded_handler(request, exc)

        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_handler_includes_retry_after(self) -> None:
        """Test handler includes Retry-After header."""
        from unittest.mock import MagicMock, patch

        from infrastructure.security.rate_limit.limiter import (
            rate_limit_exceeded_handler,
        )

        request = MagicMock()
        request.url = "http://example.com/api/test"
        request.headers = {}

        # Create mock exception with detail attribute
        exc = MagicMock()
        exc.detail = "Rate limit exceeded"

        with patch(
            "infrastructure.security.rate_limit.limiter.get_sliding_limiter"
        ) as mock_limiter:
            mock_limiter.return_value.get_state.return_value = None
            with patch(
                "infrastructure.security.rate_limit.limiter.get_remote_address"
            ) as mock_remote:
                mock_remote.return_value = "127.0.0.1"
                response = await rate_limit_exceeded_handler(request, exc)

        assert "Retry-After" in response.headers
