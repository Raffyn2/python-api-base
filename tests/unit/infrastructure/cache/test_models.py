"""Unit tests for cache models.

Tests CacheKey, CacheEntry, and CacheStats dataclasses.
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.cache.core.models import CacheEntry, CacheKey, CacheStats


class TestCacheKey:
    """Tests for CacheKey dataclass."""

    def test_creation(self) -> None:
        """Test CacheKey creation."""
        key = CacheKey[str](pattern="user:{user_id}")

        assert key.pattern == "user:{user_id}"

    def test_format(self) -> None:
        """Test key formatting with values."""
        key = CacheKey[str](pattern="user:{user_id}:profile")

        formatted = key.format(user_id="123")

        assert formatted == "user:123:profile"

    def test_format_multiple_values(self) -> None:
        """Test key formatting with multiple values."""
        key = CacheKey[dict](pattern="org:{org_id}:user:{user_id}")

        formatted = key.format(org_id="abc", user_id="xyz")

        assert formatted == "org:abc:user:xyz"

    def test_str(self) -> None:
        """Test string representation."""
        key = CacheKey[str](pattern="test:key")

        assert str(key) == "test:key"

    def test_immutability(self) -> None:
        """Test that CacheKey is immutable."""
        key = CacheKey[str](pattern="test")

        with pytest.raises(AttributeError):
            key.pattern = "new"  # type: ignore

    def test_equality(self) -> None:
        """Test CacheKey equality."""
        key1 = CacheKey[str](pattern="test")
        key2 = CacheKey[str](pattern="test")
        key3 = CacheKey[str](pattern="other")

        assert key1 == key2
        assert key1 != key3


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_creation(self) -> None:
        """Test CacheEntry creation."""
        now = datetime.now(UTC)
        entry = CacheEntry[str](
            key="test:key",
            value="test_value",
            created_at=now,
        )

        assert entry.key == "test:key"
        assert entry.value == "test_value"
        assert entry.created_at == now
        assert entry.ttl is None
        assert entry.expires_at is None
        assert entry.tags == ()

    def test_creation_with_all_fields(self) -> None:
        """Test CacheEntry creation with all fields."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)

        entry = CacheEntry[dict](
            key="user:123",
            value={"name": "test"},
            created_at=now,
            ttl=3600,
            expires_at=expires,
            tags=("user", "profile"),
        )

        assert entry.key == "user:123"
        assert entry.value == {"name": "test"}
        assert entry.ttl == 3600
        assert entry.expires_at == expires
        assert entry.tags == ("user", "profile")

    def test_is_expired_no_expiration(self) -> None:
        """Test is_expired returns False when no expiration."""
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=datetime.now(UTC),
            expires_at=None,
        )

        assert entry.is_expired is False

    def test_is_expired_not_expired(self) -> None:
        """Test is_expired returns False when not expired."""
        now = datetime.now(UTC)
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )

        assert entry.is_expired is False

    def test_is_expired_expired(self) -> None:
        """Test is_expired returns True when expired."""
        now = datetime.now(UTC)
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )

        assert entry.is_expired is True

    def test_immutability(self) -> None:
        """Test that CacheEntry is immutable."""
        entry = CacheEntry[str](
            key="test",
            value="value",
            created_at=datetime.now(UTC),
        )

        with pytest.raises(AttributeError):
            entry.value = "new"  # type: ignore

    def test_different_value_types(self) -> None:
        """Test CacheEntry with different value types."""
        now = datetime.now(UTC)

        # String
        entry_str = CacheEntry[str](key="k1", value="string", created_at=now)
        assert entry_str.value == "string"

        # List
        entry_list = CacheEntry[list](key="k2", value=[1, 2, 3], created_at=now)
        assert entry_list.value == [1, 2, 3]

        # Dict
        entry_dict = CacheEntry[dict](key="k3", value={"a": 1}, created_at=now)
        assert entry_dict.value == {"a": 1}


class TestCacheStats:
    """Tests for CacheStats dataclass."""

    def test_creation(self) -> None:
        """Test CacheStats creation."""
        stats = CacheStats(
            hits=100,
            misses=20,
            hit_rate=0.833,
            memory_usage_bytes=1024000,
            entry_count=500,
        )

        assert stats.hits == 100
        assert stats.misses == 20
        assert stats.hit_rate == 0.833
        assert stats.memory_usage_bytes == 1024000
        assert stats.entry_count == 500

    def test_immutability(self) -> None:
        """Test that CacheStats is immutable."""
        stats = CacheStats(
            hits=100,
            misses=20,
            hit_rate=0.833,
            memory_usage_bytes=1024000,
            entry_count=500,
        )

        with pytest.raises(AttributeError):
            stats.hits = 200  # type: ignore

    def test_zero_stats(self) -> None:
        """Test CacheStats with zero values."""
        stats = CacheStats(
            hits=0,
            misses=0,
            hit_rate=0.0,
            memory_usage_bytes=0,
            entry_count=0,
        )

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0

    def test_equality(self) -> None:
        """Test CacheStats equality."""
        stats1 = CacheStats(hits=100, misses=20, hit_rate=0.833, memory_usage_bytes=1024, entry_count=50)
        stats2 = CacheStats(hits=100, misses=20, hit_rate=0.833, memory_usage_bytes=1024, entry_count=50)
        stats3 = CacheStats(hits=200, misses=20, hit_rate=0.9, memory_usage_bytes=1024, entry_count=50)

        assert stats1 == stats2
        assert stats1 != stats3
