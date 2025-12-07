"""Unit tests for IdempotencyMiddleware.

Tests idempotency cache and middleware functionality.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest

from application.common.middleware.operations.idempotency_middleware import (
    IdempotencyCache,
    IdempotencyConfig,
    IdempotencyMiddleware,
    InMemoryIdempotencyCache,
)


@dataclass
class SampleCommand:
    """Sample command without idempotency key."""

    name: str


@dataclass
class IdempotentCommand:
    """Command with idempotency key attribute."""

    name: str
    idempotency_key: str


class CommandWithMethod:
    """Command with get_idempotency_key method."""

    def __init__(self, name: str, key: str) -> None:
        self.name = name
        self._key = key

    def get_idempotency_key(self) -> str:
        return self._key


class TestInMemoryIdempotencyCache:
    """Tests for InMemoryIdempotencyCache."""

    @pytest.fixture
    def cache(self) -> InMemoryIdempotencyCache:
        """Create cache instance."""
        return InMemoryIdempotencyCache()

    @pytest.mark.asyncio
    async def test_get_missing_key(self, cache: InMemoryIdempotencyCache) -> None:
        """Test get returns None for missing key."""
        result = await cache.get("missing")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: InMemoryIdempotencyCache) -> None:
        """Test set and get value."""
        await cache.set("key1", {"result": "value"}, ttl=3600)

        result = await cache.get("key1")

        assert result == {"result": "value"}

    @pytest.mark.asyncio
    async def test_get_expired_key(self, cache: InMemoryIdempotencyCache) -> None:
        """Test get returns None for expired key."""
        # Set with 0 TTL (already expired)
        await cache.set("key1", "value", ttl=0)

        # Manually expire
        cache._cache["key1"] = ("value", datetime.now(UTC) - timedelta(seconds=1))

        result = await cache.get("key1")

        assert result is None
        assert "key1" not in cache._cache

    @pytest.mark.asyncio
    async def test_exists_true(self, cache: InMemoryIdempotencyCache) -> None:
        """Test exists returns True for existing key."""
        await cache.set("key1", "value", ttl=3600)

        result = await cache.exists("key1")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, cache: InMemoryIdempotencyCache) -> None:
        """Test exists returns False for missing key."""
        result = await cache.exists("missing")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_expired(self, cache: InMemoryIdempotencyCache) -> None:
        """Test exists returns False for expired key."""
        await cache.set("key1", "value", ttl=0)
        cache._cache["key1"] = ("value", datetime.now(UTC) - timedelta(seconds=1))

        result = await cache.exists("key1")

        assert result is False

    def test_cleanup_removes_expired(self, cache: InMemoryIdempotencyCache) -> None:
        """Test cleanup removes expired entries."""
        now = datetime.now(UTC)
        cache._cache["expired1"] = ("v1", now - timedelta(seconds=10))
        cache._cache["expired2"] = ("v2", now - timedelta(seconds=5))
        cache._cache["valid"] = ("v3", now + timedelta(seconds=100))

        removed = cache.cleanup()

        assert removed == 2
        assert "expired1" not in cache._cache
        assert "expired2" not in cache._cache
        assert "valid" in cache._cache

    def test_cleanup_empty_cache(self, cache: InMemoryIdempotencyCache) -> None:
        """Test cleanup on empty cache."""
        removed = cache.cleanup()

        assert removed == 0


class TestIdempotencyConfig:
    """Tests for IdempotencyConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = IdempotencyConfig()

        assert config.ttl_seconds == 3600
        assert config.key_prefix == "idempotency"
        assert config.header_name == "X-Idempotency-Key"

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = IdempotencyConfig(
            ttl_seconds=7200,
            key_prefix="custom",
            header_name="X-Custom-Key",
        )

        assert config.ttl_seconds == 7200
        assert config.key_prefix == "custom"
        assert config.header_name == "X-Custom-Key"


class TestIdempotencyMiddleware:
    """Tests for IdempotencyMiddleware."""

    @pytest.fixture
    def cache(self) -> InMemoryIdempotencyCache:
        """Create cache instance."""
        return InMemoryIdempotencyCache()

    @pytest.fixture
    def middleware(self, cache: InMemoryIdempotencyCache) -> IdempotencyMiddleware:
        """Create middleware instance."""
        return IdempotencyMiddleware(cache)

    @pytest.mark.asyncio
    async def test_executes_handler_without_idempotency_key(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test middleware executes handler when no idempotency key."""
        command = SampleCommand(name="test")
        handler = AsyncMock(return_value="result")

        result = await middleware(command, handler)

        handler.assert_called_once_with(command)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_executes_handler_with_idempotency_key(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test middleware executes handler with idempotency key."""
        command = IdempotentCommand(name="test", idempotency_key="key-123")
        handler = AsyncMock(return_value="result")

        result = await middleware(command, handler)

        handler.assert_called_once_with(command)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_caches_result(
        self, middleware: IdempotencyMiddleware, cache: InMemoryIdempotencyCache
    ) -> None:
        """Test middleware caches result."""
        command = IdempotentCommand(name="test", idempotency_key="key-123")
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        cached = await cache.get("idempotency:IdempotentCommand:key-123")
        assert cached == "result"

    @pytest.mark.asyncio
    async def test_returns_cached_result(
        self, middleware: IdempotencyMiddleware, cache: InMemoryIdempotencyCache
    ) -> None:
        """Test middleware returns cached result on duplicate."""
        command = IdempotentCommand(name="test", idempotency_key="key-123")
        handler = AsyncMock(return_value="result")

        # First call
        await middleware(command, handler)

        # Second call with same key
        handler.reset_mock()
        handler.return_value = "new_result"
        result = await middleware(command, handler)

        handler.assert_not_called()
        assert result == "result"  # Returns cached, not new

    @pytest.mark.asyncio
    async def test_uses_get_idempotency_key_method(
        self, middleware: IdempotencyMiddleware
    ) -> None:
        """Test middleware uses get_idempotency_key method."""
        command = CommandWithMethod(name="test", key="method-key")
        handler = AsyncMock(return_value="result")

        result = await middleware(command, handler)

        handler.assert_called_once()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_logs_cache_hit(
        self,
        middleware: IdempotencyMiddleware,
        cache: InMemoryIdempotencyCache,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test middleware logs cache hit."""
        command = IdempotentCommand(name="test", idempotency_key="key-123")
        handler = AsyncMock(return_value="result")

        # First call to cache
        await middleware(command, handler)

        # Second call should hit cache
        with caplog.at_level(logging.INFO):
            await middleware(command, handler)

        assert "cached result" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_custom_config(self, cache: InMemoryIdempotencyCache) -> None:
        """Test middleware with custom config."""
        config = IdempotencyConfig(ttl_seconds=60, key_prefix="custom")
        middleware = IdempotencyMiddleware(cache, config)
        command = IdempotentCommand(name="test", idempotency_key="key-123")
        handler = AsyncMock(return_value="result")

        await middleware(command, handler)

        cached = await cache.get("custom:IdempotentCommand:key-123")
        assert cached == "result"


class TestIdempotencyCacheProtocol:
    """Tests for IdempotencyCache protocol."""

    def test_in_memory_cache_implements_protocol(self) -> None:
        """Test InMemoryIdempotencyCache implements protocol."""
        cache = InMemoryIdempotencyCache()

        assert isinstance(cache, IdempotencyCache)
