"""Unit tests for LRU local cache provider.

**Task: Phase 4 - Infrastructure Layer Tests**
**Requirements: 10.1, 10.2, 10.3, 10.4**
"""

import time
from unittest.mock import patch

import pytest

from infrastructure.cache.providers.local import LRUCache


class TestLRUCache:
    """Tests for LRUCache."""

    @pytest.fixture
    def cache(self) -> LRUCache[str, str]:
        """Create cache instance."""
        return LRUCache[str, str](max_size=5)

    def test_set_and_get(self, cache: LRUCache[str, str]) -> None:
        """Should set and get values."""
        cache.set("key1", "value1")

        result = cache.get("key1")

        assert result == "value1"

    def test_get_nonexistent_key(self, cache: LRUCache[str, str]) -> None:
        """Should return None for nonexistent key."""
        result = cache.get("nonexistent")

        assert result is None

    def test_set_with_ttl(self, cache: LRUCache[str, str]) -> None:
        """Should expire value after TTL."""
        cache.set("key1", "value1", ttl=1)

        # Value should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Value should be expired
        assert cache.get("key1") is None

    def test_set_updates_existing_key(self, cache: LRUCache[str, str]) -> None:
        """Should update existing key."""
        cache.set("key1", "value1")
        cache.set("key1", "value2")

        assert cache.get("key1") == "value2"

    def test_lru_eviction(self) -> None:
        """Should evict least recently used items."""
        cache: LRUCache[str, str] = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new key, should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still exists
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # Still exists
        assert cache.get("key4") == "value4"  # New key

    def test_delete(self, cache: LRUCache[str, str]) -> None:
        """Should delete key."""
        cache.set("key1", "value1")

        result = cache.delete("key1")

        assert result is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self, cache: LRUCache[str, str]) -> None:
        """Should return False for nonexistent key."""
        result = cache.delete("nonexistent")

        assert result is False

    def test_clear(self, cache: LRUCache[str, str]) -> None:
        """Should clear all values."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.size() == 0

    def test_size(self, cache: LRUCache[str, str]) -> None:
        """Should return correct size."""
        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_keys(self, cache: LRUCache[str, str]) -> None:
        """Should return all keys."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        keys = cache.keys()

        assert set(keys) == {"key1", "key2"}

    def test_get_many(self, cache: LRUCache[str, str]) -> None:
        """Should get multiple values."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        result = cache.get_many(["key1", "key2", "nonexistent"])

        assert result == {"key1": "value1", "key2": "value2"}

    def test_set_many(self, cache: LRUCache[str, str]) -> None:
        """Should set multiple values."""
        cache.set_many({"key1": "value1", "key2": "value2"})

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_set_many_with_ttl(self, cache: LRUCache[str, str]) -> None:
        """Should set multiple values with TTL."""
        cache.set_many({"key1": "value1", "key2": "value2"}, ttl=1)

        assert cache.get("key1") == "value1"

        time.sleep(1.1)

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_set_with_tags(self, cache: LRUCache[str, str]) -> None:
        """Should set value with tags."""
        cache.set("key1", "value1", tags=["tag1", "tag2"])
        cache.set("key2", "value2", tags=["tag1"])

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_invalidate_by_tag(self, cache: LRUCache[str, str]) -> None:
        """Should invalidate all entries with tag."""
        cache.set("key1", "value1", tags=["tag1", "tag2"])
        cache.set("key2", "value2", tags=["tag1"])
        cache.set("key3", "value3", tags=["tag2"])

        count = cache.invalidate_by_tag("tag1")

        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"  # Only has tag2

    def test_invalidate_by_nonexistent_tag(self, cache: LRUCache[str, str]) -> None:
        """Should return 0 for nonexistent tag."""
        cache.set("key1", "value1", tags=["tag1"])

        count = cache.invalidate_by_tag("nonexistent")

        assert count == 0
        assert cache.get("key1") == "value1"

    def test_eviction_removes_from_tags(self) -> None:
        """Should remove evicted keys from tag sets."""
        cache: LRUCache[str, str] = LRUCache(max_size=2)

        cache.set("key1", "value1", tags=["tag1"])
        cache.set("key2", "value2", tags=["tag1"])
        cache.set("key3", "value3", tags=["tag1"])  # Evicts key1

        # key1 should be evicted and removed from tags
        count = cache.invalidate_by_tag("tag1")

        # Only key2 and key3 should be invalidated
        assert count == 2

    def test_delete_removes_from_tags(self, cache: LRUCache[str, str]) -> None:
        """Should remove deleted keys from tag sets."""
        cache.set("key1", "value1", tags=["tag1"])
        cache.set("key2", "value2", tags=["tag1"])

        cache.delete("key1")

        count = cache.invalidate_by_tag("tag1")

        assert count == 1  # Only key2

    def test_clear_removes_tags(self, cache: LRUCache[str, str]) -> None:
        """Should clear tags when clearing cache."""
        cache.set("key1", "value1", tags=["tag1"])

        cache.clear()

        count = cache.invalidate_by_tag("tag1")

        assert count == 0

    def test_thread_safety(self, cache: LRUCache[str, str]) -> None:
        """Should be thread-safe for concurrent access."""
        import threading

        def writer() -> None:
            for i in range(100):
                cache.set(f"key{i}", f"value{i}")

        def reader() -> None:
            for i in range(100):
                cache.get(f"key{i}")

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should not raise any exceptions

    def test_expired_value_removed_on_get(self, cache: LRUCache[str, str]) -> None:
        """Should remove expired value when accessed."""
        cache.set("key1", "value1", ttl=1)

        time.sleep(1.1)

        # Access should remove expired entry
        result = cache.get("key1")

        assert result is None
        assert cache.size() == 0


class TestLRUCacheWithDifferentTypes:
    """Tests for LRUCache with different value types."""

    def test_with_int_values(self) -> None:
        """Should work with int values."""
        cache: LRUCache[str, int] = LRUCache()

        cache.set("count", 42)

        assert cache.get("count") == 42

    def test_with_dict_values(self) -> None:
        """Should work with dict values."""
        cache: LRUCache[str, dict] = LRUCache()

        cache.set("data", {"name": "test", "value": 123})

        result = cache.get("data")
        assert result == {"name": "test", "value": 123}

    def test_with_list_values(self) -> None:
        """Should work with list values."""
        cache: LRUCache[str, list] = LRUCache()

        cache.set("items", [1, 2, 3])

        result = cache.get("items")
        assert result == [1, 2, 3]

    def test_with_int_keys(self) -> None:
        """Should work with int keys."""
        cache: LRUCache[int, str] = LRUCache()

        cache.set(1, "one")
        cache.set(2, "two")

        assert cache.get(1) == "one"
        assert cache.get(2) == "two"
