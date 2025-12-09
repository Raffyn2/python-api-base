"""Unit tests for middleware components.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 2.4**
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from application.common.middleware.resilience.retry import (
    RetryConfig,
    RetryExhaustedError,
    RetryMiddleware,
)
from application.common.middleware.resilience.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CircuitBreakerOpenError,
    CircuitState,
)
from application.common.middleware.operations.idempotency_middleware import (
    IdempotencyConfig,
    IdempotencyMiddleware,
    InMemoryIdempotencyCache,
)
from application.common.middleware.cache.cache_invalidation import (
    CacheInvalidationStrategy,
    InvalidationRule,
)


class TestRetryMiddleware:
    """Tests for RetryMiddleware class."""

    @pytest.fixture
    def retry_middleware(self) -> RetryMiddleware:
        """Create retry middleware with default config."""
        return RetryMiddleware(RetryConfig(max_retries=3, base_delay=0.01))

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(
        self, retry_middleware: RetryMiddleware
    ) -> None:
        """Test successful execution on first attempt."""
        handler = AsyncMock(return_value="success")
        command = MagicMock()

        result = await retry_middleware(command, handler)

        assert result == "success"
        handler.assert_called_once_with(command)

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(
        self, retry_middleware: RetryMiddleware
    ) -> None:
        """Test retry on transient failure."""
        handler = AsyncMock(side_effect=[TimeoutError(), "success"])
        command = MagicMock()

        result = await retry_middleware(command, handler)

        assert result == "success"
        assert handler.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
        self, retry_middleware: RetryMiddleware
    ) -> None:
        """Test RetryExhaustedError when max retries exceeded."""
        handler = AsyncMock(side_effect=TimeoutError("timeout"))
        command = MagicMock()

        with pytest.raises(RetryExhaustedError) as exc_info:
            await retry_middleware(command, handler)

        assert exc_info.value.attempts == 4  # 1 initial + 3 retries
        assert isinstance(exc_info.value.last_error, TimeoutError)

    @pytest.mark.asyncio
    async def test_non_retryable_exception_not_retried(
        self, retry_middleware: RetryMiddleware
    ) -> None:
        """Test non-retryable exceptions are not retried."""
        handler = AsyncMock(side_effect=ValueError("not retryable"))
        command = MagicMock()

        with pytest.raises(ValueError):
            await retry_middleware(command, handler)

        handler.assert_called_once()

    def test_calculate_delay_exponential(self) -> None:
        """Test exponential backoff calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        middleware = RetryMiddleware(config)

        assert middleware._calculate_delay(0) == 1.0
        assert middleware._calculate_delay(1) == 2.0
        assert middleware._calculate_delay(2) == 4.0

    def test_calculate_delay_max_cap(self) -> None:
        """Test delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=5.0, jitter=False)
        middleware = RetryMiddleware(config)

        assert middleware._calculate_delay(10) == 5.0

    def test_is_retryable(self) -> None:
        """Test retryable exception detection."""
        middleware = RetryMiddleware()

        assert middleware._is_retryable(TimeoutError())
        assert middleware._is_retryable(ConnectionError())
        assert not middleware._is_retryable(ValueError())


class TestCircuitBreakerMiddleware:
    """Tests for CircuitBreakerMiddleware class."""

    @pytest.fixture
    def circuit_breaker(self) -> CircuitBreakerMiddleware:
        """Create circuit breaker with test config."""
        return CircuitBreakerMiddleware(
            CircuitBreakerConfig(failure_threshold=3, recovery_timeout=0.1)
        )

    def test_initial_state_closed(self, circuit_breaker: CircuitBreakerMiddleware) -> None:
        """Test circuit starts in closed state."""
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_keeps_circuit_closed(
        self, circuit_breaker: CircuitBreakerMiddleware
    ) -> None:
        """Test successful calls keep circuit closed."""
        handler = AsyncMock(return_value="success")
        command = MagicMock()

        result = await circuit_breaker(command, handler)

        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failures_open_circuit(
        self, circuit_breaker: CircuitBreakerMiddleware
    ) -> None:
        """Test circuit opens after failure threshold."""
        handler = AsyncMock(side_effect=Exception("error"))
        command = MagicMock()

        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker(command, handler)

        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_requests(
        self, circuit_breaker: CircuitBreakerMiddleware
    ) -> None:
        """Test open circuit rejects requests immediately."""
        handler = AsyncMock(side_effect=Exception("error"))
        command = MagicMock()

        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker(command, handler)

        # Next request should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker(command, handler)

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(
        self, circuit_breaker: CircuitBreakerMiddleware
    ) -> None:
        """Test circuit enters half-open state after recovery timeout."""
        handler = AsyncMock(side_effect=Exception("error"))
        command = MagicMock()

        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker(command, handler)

        # Simulate recovery timeout
        circuit_breaker._stats.last_failure_time = datetime.now(UTC) - timedelta(seconds=1)

        # Next call should be allowed (half-open)
        handler.side_effect = None
        handler.return_value = "success"
        result = await circuit_breaker(command, handler)

        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED

    def test_on_success_resets_failure_count(
        self, circuit_breaker: CircuitBreakerMiddleware
    ) -> None:
        """Test success resets failure count."""
        circuit_breaker._stats.failure_count = 2
        circuit_breaker._on_success()

        assert circuit_breaker._stats.failure_count == 0

    def test_on_failure_increments_count(
        self, circuit_breaker: CircuitBreakerMiddleware
    ) -> None:
        """Test failure increments failure count."""
        circuit_breaker._on_failure(Exception("error"))

        assert circuit_breaker._stats.failure_count == 1


class TestIdempotencyMiddleware:
    """Tests for IdempotencyMiddleware class."""

    @pytest.fixture
    def cache(self) -> InMemoryIdempotencyCache:
        """Create in-memory cache."""
        return InMemoryIdempotencyCache()

    @pytest.fixture
    def middleware(self, cache: InMemoryIdempotencyCache) -> IdempotencyMiddleware:
        """Create idempotency middleware."""
        return IdempotencyMiddleware(cache, IdempotencyConfig(ttl_seconds=60))

    @pytest.mark.asyncio
    async def test_first_request_executes(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test first request is executed."""
        handler = AsyncMock(return_value="result")
        command = MagicMock()
        command.idempotency_key = "key-123"

        result = await middleware(command, handler)

        assert result == "result"
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_request_returns_cached(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test duplicate request returns cached result."""
        handler = AsyncMock(return_value="result")
        command = MagicMock()
        command.idempotency_key = "key-123"

        # First request
        await middleware(command, handler)

        # Second request (duplicate)
        result = await middleware(command, handler)

        assert result == "result"
        handler.assert_called_once()  # Only called once

    @pytest.mark.asyncio
    async def test_no_idempotency_key_executes(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test request without idempotency key is always executed."""
        handler = AsyncMock(return_value="result")
        command = MagicMock(spec=[])  # No idempotency_key attribute

        result = await middleware(command, handler)

        assert result == "result"
        handler.assert_called_once()

    def test_get_idempotency_key_from_attribute(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test extracting idempotency key from attribute."""
        command = MagicMock()
        command.idempotency_key = "key-123"

        key = middleware._get_idempotency_key(command)

        assert key == "key-123"

    def test_get_idempotency_key_from_method(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test extracting idempotency key from method."""
        command = MagicMock(spec=["get_idempotency_key"])
        command.get_idempotency_key.return_value = "key-456"
        command.idempotency_key = None

        key = middleware._get_idempotency_key(command)

        assert key == "key-456"


class TestInMemoryIdempotencyCache:
    """Tests for InMemoryIdempotencyCache class."""

    @pytest.fixture
    def cache(self) -> InMemoryIdempotencyCache:
        """Create cache instance."""
        return InMemoryIdempotencyCache()

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: InMemoryIdempotencyCache) -> None:
        """Test setting and getting values."""
        await cache.set("key", "value", ttl=60)
        result = await cache.get("key")

        assert result == "value"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache: InMemoryIdempotencyCache) -> None:
        """Test getting nonexistent key returns None."""
        result = await cache.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self, cache: InMemoryIdempotencyCache) -> None:
        """Test exists check."""
        await cache.set("key", "value", ttl=60)

        assert await cache.exists("key") is True
        assert await cache.exists("nonexistent") is False

    def test_cleanup_removes_expired(self, cache: InMemoryIdempotencyCache) -> None:
        """Test cleanup removes expired entries."""
        # Add expired entry
        cache._cache["expired"] = ("value", datetime.now(UTC) - timedelta(seconds=1))
        cache._cache["valid"] = ("value", datetime.now(UTC) + timedelta(seconds=60))

        removed = cache.cleanup()

        assert removed == 1
        assert "expired" not in cache._cache
        assert "valid" in cache._cache


class TestCacheInvalidationStrategy:
    """Tests for CacheInvalidationStrategy class."""

    @pytest.fixture
    def mock_cache(self) -> MagicMock:
        """Create mock cache."""
        cache = MagicMock()
        cache.clear_pattern = AsyncMock(return_value=5)
        return cache

    @pytest.mark.asyncio
    async def test_invalidate_with_matching_rule(
        self, mock_cache: MagicMock
    ) -> None:
        """Test cache invalidation with matching rule."""

        class TestEvent:
            pass

        class TestStrategy(CacheInvalidationStrategy):
            pass

        strategy = TestStrategy(mock_cache)
        strategy.add_rule(
            InvalidationRule(
                event_type=TestEvent,
                patterns=["pattern1:*", "pattern2:*"],
            )
        )

        await strategy.invalidate(TestEvent())

        assert mock_cache.clear_pattern.call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_no_matching_rule(
        self, mock_cache: MagicMock
    ) -> None:
        """Test no invalidation when no matching rule."""

        class TestEvent:
            pass

        class OtherEvent:
            pass

        class TestStrategy(CacheInvalidationStrategy):
            pass

        strategy = TestStrategy(mock_cache)
        strategy.add_rule(
            InvalidationRule(event_type=TestEvent, patterns=["pattern:*"])
        )

        await strategy.invalidate(OtherEvent())

        mock_cache.clear_pattern.assert_not_called()


class TestRetryMiddlewareProperties:
    """Property-based tests for RetryMiddleware.

    **Feature: test-coverage-80-percent-v3, Property 4: Middleware Retry Behavior**
    **Validates: Requirements 2.4**
    """

    @given(
        max_retries=st.integers(min_value=1, max_value=5),
        failures_before_success=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_retries_until_success_or_exhausted(
        self, max_retries: int, failures_before_success: int
    ) -> None:
        """Property: Retry middleware attempts up to max_retries times.

        **Feature: test-coverage-80-percent-v3, Property 4: Middleware Retry Behavior**
        **Validates: Requirements 2.4**
        """
        config = RetryConfig(max_retries=max_retries, base_delay=0.001, jitter=False)
        middleware = RetryMiddleware(config)

        call_count = 0

        async def handler(cmd: Any) -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= failures_before_success:
                raise TimeoutError("transient")
            return "success"

        command = MagicMock()

        if failures_before_success <= max_retries:
            result = await middleware(command, handler)
            assert result == "success"
            assert call_count == failures_before_success + 1
        else:
            with pytest.raises(RetryExhaustedError):
                await middleware(command, handler)
            assert call_count == max_retries + 1
