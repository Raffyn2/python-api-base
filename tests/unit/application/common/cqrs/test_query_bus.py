"""Unit tests for QueryBus.

Tests query registration, dispatch, and caching.
"""

from unittest.mock import AsyncMock

import pytest

from application.common.cqrs import (
    HandlerNotFoundError,
    Query,
    QueryBus,
)


class GetUserQuery(Query[dict[str, str]]):
    """Test query for getting a user."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

    async def execute(self) -> dict[str, str]:
        return {"id": self.user_id, "name": "Test User"}


class CacheableQuery(Query[str]):
    """Test query with caching enabled."""

    cacheable = True
    cache_ttl = 60

    def __init__(self, key: str) -> None:
        self.key = key

    async def execute(self) -> str:
        return f"Result for {self.key}"


class CustomCacheKeyQuery(Query[str]):
    """Test query with custom cache key."""

    def __init__(self, key: str) -> None:
        self.key = key
        self.cache_key = f"custom:{key}"

    async def execute(self) -> str:
        return f"Result for {self.key}"


class TestQueryBusRegistration:
    """Tests for query handler registration."""

    def test_register_handler(self) -> None:
        """Test registering a query handler."""
        bus = QueryBus()

        async def handler(query: GetUserQuery) -> dict[str, str]:
            return {"id": query.user_id}

        bus.register(GetUserQuery, handler)
        assert GetUserQuery in bus._handlers

    def test_register_duplicate_handler_raises(self) -> None:
        """Test that registering duplicate handler raises ValueError."""
        bus = QueryBus()

        async def handler(query: GetUserQuery) -> dict[str, str]:
            return {}

        bus.register(GetUserQuery, handler)

        with pytest.raises(ValueError, match="Handler already registered"):
            bus.register(GetUserQuery, handler)

    def test_unregister_handler(self) -> None:
        """Test unregistering a query handler."""
        bus = QueryBus()

        async def handler(query: GetUserQuery) -> dict[str, str]:
            return {}

        bus.register(GetUserQuery, handler)
        bus.unregister(GetUserQuery)
        assert GetUserQuery not in bus._handlers

    def test_unregister_nonexistent_handler(self) -> None:
        """Test unregistering non-existent handler does not raise."""
        bus = QueryBus()
        bus.unregister(GetUserQuery)  # Should not raise


class TestQueryBusDispatch:
    """Tests for query dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_query(self) -> None:
        """Test dispatching a query to its handler."""
        bus = QueryBus()

        async def handler(query: GetUserQuery) -> dict[str, str]:
            return {"id": query.user_id, "name": "John"}

        bus.register(GetUserQuery, handler)
        result = await bus.dispatch(GetUserQuery("123"))

        assert result == {"id": "123", "name": "John"}

    @pytest.mark.asyncio
    async def test_dispatch_unregistered_query_raises(self) -> None:
        """Test dispatching unregistered query raises HandlerNotFoundError."""
        bus = QueryBus()

        with pytest.raises(HandlerNotFoundError):
            await bus.dispatch(GetUserQuery("123"))


class TestQueryBusCaching:
    """Tests for query caching."""

    def test_set_cache(self) -> None:
        """Test setting cache provider."""
        bus = QueryBus()
        cache = AsyncMock()

        bus.set_cache(cache)

        assert bus._cache is cache

    def test_cache_initially_none(self) -> None:
        """Test cache is None by default."""
        bus = QueryBus()
        assert bus._cache is None


class TestQueryBusCacheKey:
    """Tests for cache key generation."""

    def test_get_cache_key_with_custom_key(self) -> None:
        """Test cache key from query with cache_key attribute."""
        bus = QueryBus()
        query = CustomCacheKeyQuery("test")

        key = bus._get_cache_key(query)

        assert key == "custom:test"

    def test_get_cache_key_cacheable_query(self) -> None:
        """Test cache key generation for cacheable query."""
        bus = QueryBus()
        query = CacheableQuery("test")

        key = bus._get_cache_key(query)

        assert key is not None
        assert "CacheableQuery" in key

    def test_get_cache_key_non_cacheable_returns_none(self) -> None:
        """Test non-cacheable query returns None cache key."""
        bus = QueryBus()
        query = GetUserQuery("123")

        key = bus._get_cache_key(query)

        assert key is None
