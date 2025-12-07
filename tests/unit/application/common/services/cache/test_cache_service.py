"""Tests for cache service.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.common.services.cache.cache_service import CacheService


class MockCache:
    """Mock cache for testing."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.get = AsyncMock(side_effect=self._get)
        self.set = AsyncMock(side_effect=self._set)
        self.delete = AsyncMock(side_effect=self._delete)

    async def _get(self, key: str) -> Any | None:
        return self.data.get(key)

    async def _set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self.data[key] = value

    async def _delete(self, key: str) -> None:
        self.data.pop(key, None)


class TestCacheService:
    """Tests for CacheService."""

    def test_create_without_cache(self) -> None:
        """Test creating service without cache client."""
        service = CacheService()
        assert service.is_enabled is False

    def test_create_with_cache(self) -> None:
        """Test creating service with cache client."""
        cache = MockCache()
        service = CacheService(cache=cache)
        assert service.is_enabled is True

    def test_create_with_prefix(self) -> None:
        """Test creating service with prefix."""
        cache = MockCache()
        service = CacheService(cache=cache, prefix="items")
        assert service._prefix == "items"

    def test_create_with_custom_list_key(self) -> None:
        """Test creating service with custom list key."""
        cache = MockCache()
        service = CacheService(cache=cache, list_key="all")
        assert service._list_key == "all"

    def test_make_key_with_prefix(self) -> None:
        """Test key generation with prefix."""
        service = CacheService(prefix="users")
        key = service._make_key("123")
        assert key == "users:123"

    def test_make_key_without_prefix(self) -> None:
        """Test key generation without prefix."""
        service = CacheService()
        key = service._make_key("123")
        assert key == "123"

    def test_list_cache_key(self) -> None:
        """Test list cache key generation."""
        service = CacheService(prefix="items", list_key="list")
        key = service._list_cache_key()
        assert key == "items:list"

    @pytest.mark.asyncio
    async def test_get_returns_none_when_disabled(self) -> None:
        """Test get returns None when cache is disabled."""
        service = CacheService()
        result = await service.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_cached_value(self) -> None:
        """Test get returns cached value."""
        cache = MockCache()
        cache.data["items:123"] = {"id": "123", "name": "Test"}
        service = CacheService(cache=cache, prefix="items")

        result = await service.get("123")
        assert result == {"id": "123", "name": "Test"}

    @pytest.mark.asyncio
    async def test_get_returns_none_on_miss(self) -> None:
        """Test get returns None on cache miss."""
        cache = MockCache()
        service = CacheService(cache=cache, prefix="items")

        result = await service.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_handles_exception(self) -> None:
        """Test get handles exception gracefully."""
        cache = MockCache()
        cache.get = AsyncMock(side_effect=Exception("Cache error"))
        service = CacheService(cache=cache)

        result = await service.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_does_nothing_when_disabled(self) -> None:
        """Test set does nothing when cache is disabled."""
        service = CacheService()
        await service.set("key", "value")
        # Should not raise

    @pytest.mark.asyncio
    async def test_set_stores_value(self) -> None:
        """Test set stores value in cache."""
        cache = MockCache()
        service = CacheService(cache=cache, prefix="items")

        await service.set("123", {"name": "Test"})

        assert cache.data["items:123"] == {"name": "Test"}

    @pytest.mark.asyncio
    async def test_set_with_ttl(self) -> None:
        """Test set with custom TTL."""
        cache = MockCache()
        service = CacheService(cache=cache)

        await service.set("key", "value", ttl=600)

        cache.set.assert_called_once()
        call_args = cache.set.call_args
        assert call_args[0][2] == 600  # TTL argument

    @pytest.mark.asyncio
    async def test_set_handles_exception(self) -> None:
        """Test set handles exception gracefully."""
        cache = MockCache()
        cache.set = AsyncMock(side_effect=Exception("Cache error"))
        service = CacheService(cache=cache)

        # Should not raise
        await service.set("key", "value")

    @pytest.mark.asyncio
    async def test_delete_does_nothing_when_disabled(self) -> None:
        """Test delete does nothing when cache is disabled."""
        service = CacheService()
        await service.delete("key")
        # Should not raise

    @pytest.mark.asyncio
    async def test_delete_removes_value(self) -> None:
        """Test delete removes value from cache."""
        cache = MockCache()
        cache.data["items:123"] = {"name": "Test"}
        service = CacheService(cache=cache, prefix="items")

        await service.delete("123")

        assert "items:123" not in cache.data

    @pytest.mark.asyncio
    async def test_delete_handles_exception(self) -> None:
        """Test delete handles exception gracefully."""
        cache = MockCache()
        cache.delete = AsyncMock(side_effect=Exception("Cache error"))
        service = CacheService(cache=cache)

        # Should not raise
        await service.delete("key")

    @pytest.mark.asyncio
    async def test_invalidate_deletes_key(self) -> None:
        """Test invalidate deletes the key."""
        cache = MockCache()
        cache.data["items:123"] = {"name": "Test"}
        service = CacheService(cache=cache, prefix="items")

        await service.invalidate("123", invalidate_list=False)

        assert "items:123" not in cache.data

    @pytest.mark.asyncio
    async def test_invalidate_also_deletes_list(self) -> None:
        """Test invalidate also deletes list cache."""
        cache = MockCache()
        cache.data["items:123"] = {"name": "Test"}
        cache.data["items:list"] = [{"id": "123"}]
        service = CacheService(cache=cache, prefix="items")

        await service.invalidate("123", invalidate_list=True)

        assert "items:123" not in cache.data
        assert "items:list" not in cache.data

    @pytest.mark.asyncio
    async def test_invalidate_skips_list_when_disabled(self) -> None:
        """Test invalidate skips list when invalidate_list=False."""
        cache = MockCache()
        cache.data["items:123"] = {"name": "Test"}
        cache.data["items:list"] = [{"id": "123"}]
        service = CacheService(cache=cache, prefix="items")

        await service.invalidate("123", invalidate_list=False)

        assert "items:123" not in cache.data
        assert "items:list" in cache.data  # List should remain
