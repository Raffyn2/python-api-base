"""Unit tests for cache decorators.

Tests caching, invalidation, and pattern invalidation decorators.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.cache.decorators import (
    cached,
    get_default_cache,
    invalidate_cache,
    invalidate_pattern,
    set_default_cache,
)


class TestCachedDecorator:
    """Tests for @cached decorator."""

    @pytest.mark.asyncio
    async def test_cache_miss_calls_function(self) -> None:
        """Test cache miss executes function and caches result."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        class TestUseCase:
            def __init__(self):
                self._redis = mock_redis
                self.call_count = 0

            @cached("test", ttl=60)
            async def get_item(self, item_id: str) -> dict:
                self.call_count += 1
                return {"id": item_id}

        use_case = TestUseCase()
        result = await use_case.get_item("123")

        assert result == {"id": "123"}
        assert use_case.call_count == 1
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_value(self) -> None:
        """Test cache hit returns cached value without calling function."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value={"id": "cached"})

        class TestUseCase:
            def __init__(self):
                self._redis = mock_redis
                self.call_count = 0

            @cached("test", ttl=60)
            async def get_item(self, item_id: str) -> dict:
                self.call_count += 1
                return {"id": item_id}

        use_case = TestUseCase()
        result = await use_case.get_item("123")

        assert result == {"id": "cached"}
        assert use_case.call_count == 0

    @pytest.mark.asyncio
    async def test_no_redis_executes_directly(self) -> None:
        """Test function executes directly when no redis available."""

        class TestUseCase:
            def __init__(self):
                self.call_count = 0

            @cached("test", ttl=60)
            async def get_item(self, item_id: str) -> dict:
                self.call_count += 1
                return {"id": item_id}

        use_case = TestUseCase()
        result = await use_case.get_item("123")

        assert result == {"id": "123"}
        assert use_case.call_count == 1

    @pytest.mark.asyncio
    async def test_custom_key_builder(self) -> None:
        """Test custom key builder is used."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        def custom_key(item_id: str) -> str:
            return f"custom:{item_id}"

        class TestUseCase:
            def __init__(self):
                self._redis = mock_redis

            @cached("test", ttl=60, key_builder=custom_key)
            async def get_item(self, item_id: str) -> dict:
                return {"id": item_id}

        use_case = TestUseCase()
        await use_case.get_item("123")

        mock_redis.get.assert_called_once_with("custom:123")


class TestInvalidateCacheDecorator:
    """Tests for @invalidate_cache decorator."""

    @pytest.mark.asyncio
    async def test_invalidates_cache_after_execution(self) -> None:
        """Test cache is invalidated after function execution."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()

        class TestUseCase:
            def __init__(self):
                self._redis = mock_redis

            @invalidate_cache("test")
            async def update_item(self, item_id: str, data: dict) -> dict:
                return {"id": item_id, **data}

        use_case = TestUseCase()
        result = await use_case.update_item("123", {"name": "updated"})

        assert result == {"id": "123", "name": "updated"}
        mock_redis.delete.assert_called_once_with("test:123")

    @pytest.mark.asyncio
    async def test_no_redis_skips_invalidation(self) -> None:
        """Test invalidation is skipped when no redis available."""

        class TestUseCase:
            @invalidate_cache("test")
            async def update_item(self, item_id: str) -> dict:
                return {"id": item_id}

        use_case = TestUseCase()
        result = await use_case.update_item("123")

        assert result == {"id": "123"}


class TestInvalidatePatternDecorator:
    """Tests for @invalidate_pattern decorator."""

    @pytest.mark.asyncio
    async def test_invalidates_pattern_after_execution(self) -> None:
        """Test pattern is invalidated after function execution."""
        mock_redis = AsyncMock()
        mock_redis.delete_pattern = AsyncMock(return_value=5)

        class TestUseCase:
            def __init__(self):
                self._redis = mock_redis

            @invalidate_pattern("test:*")
            async def clear_all(self) -> str:
                return "cleared"

        use_case = TestUseCase()
        result = await use_case.clear_all()

        assert result == "cleared"
        mock_redis.delete_pattern.assert_called_once_with("test:*")


class TestDefaultCache:
    """Tests for default cache management."""

    def test_get_default_cache_initially_none(self) -> None:
        """Test default cache is None initially."""
        # Reset to ensure clean state
        set_default_cache(None)
        assert get_default_cache() is None

    def test_set_and_get_default_cache(self) -> None:
        """Test setting and getting default cache."""
        mock_cache = MagicMock()
        set_default_cache(mock_cache)

        assert get_default_cache() is mock_cache

        # Cleanup
        set_default_cache(None)
