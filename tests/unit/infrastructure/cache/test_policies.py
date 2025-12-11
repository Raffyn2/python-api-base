"""Unit tests for cache policies.

Tests CacheConfig and CacheEntry from policies module.
"""

import time

from infrastructure.cache.core.policies import CacheConfig, CacheEntry


class TestCacheConfigPolicies:
    """Tests for CacheConfig in policies module."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CacheConfig()

        assert config.ttl == 3600
        assert config.max_size == 1000
        assert config.key_prefix == ""

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = CacheConfig(
            ttl=7200,
            max_size=5000,
            key_prefix="app:",
        )

        assert config.ttl == 7200
        assert config.max_size == 5000
        assert config.key_prefix == "app:"

    def test_none_ttl(self) -> None:
        """Test configuration with no expiration."""
        config = CacheConfig(ttl=None)

        assert config.ttl is None


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_creation_with_value(self) -> None:
        """Test entry creation with value."""
        entry = CacheEntry(value="test_value")

        assert entry.value == "test_value"
        assert entry.ttl is None
        assert entry.created_at > 0

    def test_creation_with_ttl(self) -> None:
        """Test entry creation with TTL."""
        entry = CacheEntry(value="test", ttl=60)

        assert entry.value == "test"
        assert entry.ttl == 60

    def test_is_expired_no_ttl(self) -> None:
        """Test is_expired returns False when no TTL."""
        entry = CacheEntry(value="test", ttl=None)

        assert entry.is_expired is False

    def test_is_expired_not_expired(self) -> None:
        """Test is_expired returns False when not expired."""
        entry = CacheEntry(value="test", ttl=3600)

        assert entry.is_expired is False

    def test_is_expired_expired(self) -> None:
        """Test is_expired returns True when expired."""
        entry = CacheEntry(
            value="test",
            created_at=time.time() - 120,  # 2 minutes ago
            ttl=60,  # 1 minute TTL
        )

        assert entry.is_expired is True

    def test_remaining_ttl_no_ttl(self) -> None:
        """Test remaining_ttl returns None when no TTL."""
        entry = CacheEntry(value="test", ttl=None)

        assert entry.remaining_ttl is None

    def test_remaining_ttl_not_expired(self) -> None:
        """Test remaining_ttl returns positive value when not expired."""
        entry = CacheEntry(value="test", ttl=3600)

        remaining = entry.remaining_ttl
        assert remaining is not None
        assert remaining > 0
        assert remaining <= 3600

    def test_remaining_ttl_expired(self) -> None:
        """Test remaining_ttl returns 0 when expired."""
        entry = CacheEntry(
            value="test",
            created_at=time.time() - 120,
            ttl=60,
        )

        assert entry.remaining_ttl == 0

    def test_different_value_types(self) -> None:
        """Test entry with different value types."""
        # String
        entry_str = CacheEntry(value="string")
        assert entry_str.value == "string"

        # Dict
        entry_dict = CacheEntry(value={"key": "value"})
        assert entry_dict.value == {"key": "value"}

        # List
        entry_list = CacheEntry(value=[1, 2, 3])
        assert entry_list.value == [1, 2, 3]

        # None
        entry_none = CacheEntry(value=None)
        assert entry_none.value is None

    def test_custom_created_at(self) -> None:
        """Test entry with custom created_at timestamp."""
        custom_time = time.time() - 1000
        entry = CacheEntry(value="test", created_at=custom_time, ttl=2000)

        assert entry.created_at == custom_time
        assert entry.is_expired is False
        assert entry.remaining_ttl is not None
        assert entry.remaining_ttl > 0
