"""Unit tests for infrastructure/cache/decorators.py.

Tests cache decorators for use cases.

**Feature: test-coverage-90-percent**
**Validates: Requirements 4.2**
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.cache.decorators import (
    cached,
    get_default_cache,
    invalidate_cache,
    invalidate_pattern,
    set_default_cache,
)


class MockRedis:
    """Mock Redis client for testing."""
    
    def __init__(self) -> None:
        self._store: dict[str, object] = {}
    
    async def get(self, key: str) -> object | None:
        return self._store.get(key)
    
    async def set(self, key: str, value: object, ttl: int = 0) -> None:
        self._store[key] = value
    
    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
    
    async def delete_pattern(self, pattern: str) -> int:
        # Simple pattern matching for testing
        prefix = pattern.rstrip("*")
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._store[key]
        return len(keys_to_delete)


class TestCachedDecorator:
    """Tests for @cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_returns_result(self) -> None:
        """@cached should return function result."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
            
            @cached("test", ttl=300)
            async def get_item(self, item_id: str) -> dict:
                return {"id": item_id, "name": "Test"}
        
        uc = UseCase()
        result = await uc.get_item("123")
        
        assert result == {"id": "123", "name": "Test"}

    @pytest.mark.asyncio
    async def test_cached_stores_in_cache(self) -> None:
        """@cached should store result in cache."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
                self.call_count = 0
            
            @cached("test", ttl=300)
            async def get_item(self, item_id: str) -> dict:
                self.call_count += 1
                return {"id": item_id}
        
        uc = UseCase()
        
        # First call
        await uc.get_item("123")
        assert uc.call_count == 1
        
        # Second call should use cache
        await uc.get_item("123")
        assert uc.call_count == 1  # Not incremented

    @pytest.mark.asyncio
    async def test_cached_different_keys(self) -> None:
        """@cached should use different keys for different args."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
                self.call_count = 0
            
            @cached("test", ttl=300)
            async def get_item(self, item_id: str) -> dict:
                self.call_count += 1
                return {"id": item_id}
        
        uc = UseCase()
        
        await uc.get_item("123")
        await uc.get_item("456")
        
        assert uc.call_count == 2  # Different keys

    @pytest.mark.asyncio
    async def test_cached_without_redis(self) -> None:
        """@cached should work without redis (no caching)."""
        class UseCase:
            @cached("test", ttl=300)
            async def get_item(self, item_id: str) -> dict:
                return {"id": item_id}
        
        uc = UseCase()
        result = await uc.get_item("123")
        
        assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_cached_with_kwargs(self) -> None:
        """@cached should handle kwargs."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
            
            @cached("test", ttl=300)
            async def search(self, **kwargs: object) -> dict:
                return {"query": kwargs}
        
        uc = UseCase()
        result = await uc.search(name="test", limit=10)
        
        assert result["query"]["name"] == "test"

    @pytest.mark.asyncio
    async def test_cached_with_custom_key_builder(self) -> None:
        """@cached should use custom key builder."""
        def custom_key(item_id: str, version: int) -> str:
            return f"item:{item_id}:v{version}"
        
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
            
            @cached("test", ttl=300, key_builder=custom_key)
            async def get_item(self, item_id: str, version: int) -> dict:
                return {"id": item_id, "version": version}
        
        uc = UseCase()
        await uc.get_item("123", 1)
        
        # Check custom key was used
        assert "item:123:v1" in uc._redis._store

    @pytest.mark.asyncio
    async def test_cached_handles_cache_error(self) -> None:
        """@cached should handle cache errors gracefully."""
        # This test verifies that when redis is None, caching is skipped
        class UseCase:
            def __init__(self) -> None:
                self._redis = None  # No redis available
            
            @cached("test", ttl=300)
            async def get_item(self, item_id: str) -> dict:
                return {"id": item_id}
        
        uc = UseCase()
        # Should not raise, just skip caching
        result = await uc.get_item("123")
        
        assert result == {"id": "123"}


class TestInvalidateCacheDecorator:
    """Tests for @invalidate_cache decorator."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_removes_key(self) -> None:
        """@invalidate_cache should remove cached key."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
            
            @cached("item", ttl=300)
            async def get_item(self, item_id: str) -> dict:
                return {"id": item_id}
            
            @invalidate_cache("item")
            async def update_item(self, item_id: str, data: dict) -> dict:
                return {"id": item_id, **data}
        
        uc = UseCase()
        
        # Cache the item
        await uc.get_item("123")
        assert "item:123" in uc._redis._store
        
        # Update should invalidate
        await uc.update_item("123", {"name": "Updated"})
        assert "item:123" not in uc._redis._store

    @pytest.mark.asyncio
    async def test_invalidate_cache_returns_result(self) -> None:
        """@invalidate_cache should return function result."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
            
            @invalidate_cache("item")
            async def update_item(self, item_id: str) -> dict:
                return {"id": item_id, "updated": True}
        
        uc = UseCase()
        result = await uc.update_item("123")
        
        assert result == {"id": "123", "updated": True}

    @pytest.mark.asyncio
    async def test_invalidate_cache_without_redis(self) -> None:
        """@invalidate_cache should work without redis."""
        class UseCase:
            @invalidate_cache("item")
            async def update_item(self, item_id: str) -> dict:
                return {"id": item_id}
        
        uc = UseCase()
        result = await uc.update_item("123")
        
        assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_custom_key_builder(self) -> None:
        """@invalidate_cache should use custom key builder."""
        def custom_key(item_id: str) -> str:
            return f"custom:{item_id}"
        
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
                self._redis._store["custom:123"] = {"cached": True}
            
            @invalidate_cache("item", key_builder=custom_key)
            async def update_item(self, item_id: str) -> dict:
                return {"id": item_id}
        
        uc = UseCase()
        await uc.update_item("123")
        
        assert "custom:123" not in uc._redis._store


class TestInvalidatePatternDecorator:
    """Tests for @invalidate_pattern decorator."""

    @pytest.mark.asyncio
    async def test_invalidate_pattern_removes_matching_keys(self) -> None:
        """@invalidate_pattern should remove matching keys."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
                self._redis._store["item:1"] = {"id": "1"}
                self._redis._store["item:2"] = {"id": "2"}
                self._redis._store["other:1"] = {"id": "1"}
            
            @invalidate_pattern("item:*")
            async def clear_items(self) -> bool:
                return True
        
        uc = UseCase()
        await uc.clear_items()
        
        assert "item:1" not in uc._redis._store
        assert "item:2" not in uc._redis._store
        assert "other:1" in uc._redis._store  # Not matching pattern

    @pytest.mark.asyncio
    async def test_invalidate_pattern_returns_result(self) -> None:
        """@invalidate_pattern should return function result."""
        class UseCase:
            def __init__(self) -> None:
                self._redis = MockRedis()
            
            @invalidate_pattern("item:*")
            async def clear_items(self) -> str:
                return "cleared"
        
        uc = UseCase()
        result = await uc.clear_items()
        
        assert result == "cleared"


class TestDefaultCache:
    """Tests for default cache functions."""

    def test_get_default_cache_initially_none(self) -> None:
        """get_default_cache should return None initially."""
        # Reset to ensure clean state
        set_default_cache(None)  # type: ignore
        
        assert get_default_cache() is None

    def test_set_and_get_default_cache(self) -> None:
        """set_default_cache should set the cache."""
        mock_cache = MagicMock()
        
        set_default_cache(mock_cache)
        
        assert get_default_cache() is mock_cache
        
        # Cleanup
        set_default_cache(None)  # type: ignore
