"""Tests for query cache middleware.

Tests InMemoryQueryCache, QueryCacheConfig, and QueryCacheMiddleware.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from application.common.middleware.cache.query_cache import (
    InMemoryQueryCache,
    QueryCacheConfig,
    QueryCacheMiddleware,
)


class TestInMemoryQueryCache:
    """Tests for InMemoryQueryCache."""

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self) -> None:
        cache = InMemoryQueryCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self) -> None:
        cache = InMemoryQueryCache()
        await cache.set("key", {"data": "value"}, ttl=300)
        result = await cache.get("key")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_returns_none_for_expired_key(self) -> None:
        cache = InMemoryQueryCache()
        # Set with 0 TTL (immediately expired)
        cache._cache["key"] = ("value", datetime.now(UTC) - timedelta(seconds=1))
        result = await cache.get("key")
        assert result is None
        assert "key" not in cache._cache

    @pytest.mark.asyncio
    async def test_delete_removes_key(self) -> None:
        cache = InMemoryQueryCache()
        await cache.set("key", "value", ttl=300)
        await cache.delete("key")
        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self) -> None:
        cache = InMemoryQueryCache()
        await cache.delete("nonexistent")  # Should not raise

    @pytest.mark.asyncio
    async def test_clear_removes_all_keys(self) -> None:
        cache = InMemoryQueryCache()
        await cache.set("key1", "value1", ttl=300)
        await cache.set("key2", "value2", ttl=300)
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    def test_cleanup_removes_expired(self) -> None:
        cache = InMemoryQueryCache()
        now = datetime.now(UTC)
        cache._cache["expired"] = ("value", now - timedelta(seconds=1))
        cache._cache["valid"] = ("value", now + timedelta(seconds=300))

        removed = cache.cleanup()
        assert removed == 1
        assert "expired" not in cache._cache
        assert "valid" in cache._cache

    def test_size_returns_count(self) -> None:
        cache = InMemoryQueryCache()
        assert cache.size() == 0
        cache._cache["key1"] = ("value", datetime.now(UTC) + timedelta(seconds=300))
        cache._cache["key2"] = ("value", datetime.now(UTC) + timedelta(seconds=300))
        assert cache.size() == 2

    @pytest.mark.asyncio
    async def test_clear_pattern_prefix(self) -> None:
        cache = InMemoryQueryCache()
        await cache.set("query_cache:GetUser:1", "user1", ttl=300)
        await cache.set("query_cache:GetUser:2", "user2", ttl=300)
        await cache.set("query_cache:ListUsers:all", "users", ttl=300)

        cleared = await cache.clear_pattern("query_cache:GetUser:*")
        assert cleared == 2
        assert await cache.get("query_cache:GetUser:1") is None
        assert await cache.get("query_cache:GetUser:2") is None
        assert await cache.get("query_cache:ListUsers:all") == "users"

    @pytest.mark.asyncio
    async def test_clear_pattern_wildcard_middle(self) -> None:
        cache = InMemoryQueryCache()
        await cache.set("cache:user:123:profile", "profile", ttl=300)
        await cache.set("cache:user:123:settings", "settings", ttl=300)
        await cache.set("cache:user:456:profile", "profile2", ttl=300)

        cleared = await cache.clear_pattern("*user:123*")
        assert cleared == 2
        assert await cache.get("cache:user:456:profile") == "profile2"

    @pytest.mark.asyncio
    async def test_clear_pattern_no_matches(self) -> None:
        cache = InMemoryQueryCache()
        await cache.set("key1", "value1", ttl=300)
        cleared = await cache.clear_pattern("nonexistent:*")
        assert cleared == 0


class TestQueryCacheConfig:
    """Tests for QueryCacheConfig."""

    def test_default_values(self) -> None:
        config = QueryCacheConfig()
        assert config.ttl_seconds == 300
        assert config.key_prefix == "query_cache"
        assert config.enabled is True
        assert config.cache_all_queries is False
        assert config.log_hits is True
        assert config.log_misses is False

    def test_custom_values(self) -> None:
        config = QueryCacheConfig(
            ttl_seconds=600,
            key_prefix="custom",
            enabled=False,
            cache_all_queries=True,
        )
        assert config.ttl_seconds == 600
        assert config.key_prefix == "custom"
        assert config.enabled is False
        assert config.cache_all_queries is True

    def test_is_frozen(self) -> None:
        config = QueryCacheConfig()
        with pytest.raises(AttributeError):
            config.ttl_seconds = 100  # type: ignore


@dataclass
class SampleQuery:
    """Sample query for testing."""

    user_id: str

    def get_cache_key(self) -> str:
        return f"user:{self.user_id}"


@dataclass
class QueryWithCacheKey:
    """Query with cache_key attribute."""

    item_id: str
    cache_key: str = "static_key"


@dataclass
class QueryWithoutCache:
    """Query without caching support."""

    data: str


class TestQueryCacheMiddleware:
    """Tests for QueryCacheMiddleware."""

    @pytest.fixture()
    def cache(self) -> InMemoryQueryCache:
        return InMemoryQueryCache()

    @pytest.fixture()
    def middleware(self, cache: InMemoryQueryCache) -> QueryCacheMiddleware:
        return QueryCacheMiddleware(cache, QueryCacheConfig())

    @pytest.mark.asyncio
    async def test_cache_miss_executes_handler(self, middleware: QueryCacheMiddleware) -> None:
        query = SampleQuery(user_id="123")
        handler_called = False

        async def handler(q: Any) -> dict:
            nonlocal handler_called
            handler_called = True
            return {"id": q.user_id}

        result = await middleware(query, handler)
        assert handler_called
        assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_cache_hit_skips_handler(self, cache: InMemoryQueryCache, middleware: QueryCacheMiddleware) -> None:
        query = SampleQuery(user_id="123")
        cache_key = "query_cache:SampleQuery:user:123"
        await cache.set(cache_key, {"cached": True}, ttl=300)

        handler_called = False

        async def handler(q: Any) -> dict:
            nonlocal handler_called
            handler_called = True
            return {"id": q.user_id}

        result = await middleware(query, handler)
        assert not handler_called
        assert result == {"cached": True}

    @pytest.mark.asyncio
    async def test_caches_result_after_execution(
        self, cache: InMemoryQueryCache, middleware: QueryCacheMiddleware
    ) -> None:
        query = SampleQuery(user_id="456")

        async def handler(q: Any) -> dict:
            return {"id": q.user_id}

        await middleware(query, handler)

        # Check cache was populated
        cache_key = "query_cache:SampleQuery:user:456"
        cached = await cache.get(cache_key)
        assert cached == {"id": "456"}

    @pytest.mark.asyncio
    async def test_uses_cache_key_attribute(self, cache: InMemoryQueryCache, middleware: QueryCacheMiddleware) -> None:
        query = QueryWithCacheKey(item_id="item-1")

        async def handler(q: Any) -> dict:
            return {"item": q.item_id}

        await middleware(query, handler)

        cache_key = "query_cache:QueryWithCacheKey:static_key"
        cached = await cache.get(cache_key)
        assert cached == {"item": "item-1"}

    @pytest.mark.asyncio
    async def test_skips_caching_without_cache_key(
        self, cache: InMemoryQueryCache, middleware: QueryCacheMiddleware
    ) -> None:
        query = QueryWithoutCache(data="test")

        async def handler(q: Any) -> str:
            return q.data

        result = await middleware(query, handler)
        assert result == "test"
        assert cache.size() == 0

    @pytest.mark.asyncio
    async def test_disabled_cache_skips_caching(self, cache: InMemoryQueryCache) -> None:
        config = QueryCacheConfig(enabled=False)
        middleware = QueryCacheMiddleware(cache, config)
        query = SampleQuery(user_id="123")

        async def handler(q: Any) -> dict:
            return {"id": q.user_id}

        await middleware(query, handler)
        assert cache.size() == 0

    @pytest.mark.asyncio
    async def test_cache_all_queries_generates_key(self, cache: InMemoryQueryCache) -> None:
        config = QueryCacheConfig(cache_all_queries=True)
        middleware = QueryCacheMiddleware(cache, config)
        query = QueryWithoutCache(data="test")

        async def handler(q: Any) -> str:
            return q.data

        await middleware(query, handler)
        assert cache.size() == 1

    @pytest.mark.asyncio
    async def test_generate_cache_key_deterministic(self, cache: InMemoryQueryCache) -> None:
        config = QueryCacheConfig(cache_all_queries=True)
        middleware = QueryCacheMiddleware(cache, config)

        query1 = QueryWithoutCache(data="test")
        query2 = QueryWithoutCache(data="test")

        key1 = middleware._generate_cache_key(query1)
        key2 = middleware._generate_cache_key(query2)
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_different_queries_different_keys(self, cache: InMemoryQueryCache) -> None:
        config = QueryCacheConfig(cache_all_queries=True)
        middleware = QueryCacheMiddleware(cache, config)

        query1 = QueryWithoutCache(data="test1")
        query2 = QueryWithoutCache(data="test2")

        key1 = middleware._generate_cache_key(query1)
        key2 = middleware._generate_cache_key(query2)
        assert key1 != key2
