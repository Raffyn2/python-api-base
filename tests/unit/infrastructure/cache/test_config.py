"""Unit tests for cache configuration.

Tests CacheConfig dataclass and its default values.
"""

import pytest

from infrastructure.cache.core.config import CacheConfig


class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CacheConfig()
        
        assert config.default_ttl == 3600
        assert config.max_size == 10000
        assert config.prefix == ""
        assert config.key_prefix == ""
        assert config.serializer == "json"
        assert config.redis_url is None
        assert config.redis_db == 0
        assert config.redis_password is None
        assert config.pool_min_size == 1
        assert config.pool_max_size == 10
        assert config.options == {}

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = CacheConfig(
            default_ttl=7200,
            max_size=5000,
            prefix="app:",
            key_prefix="cache:",
            serializer="pickle",
            redis_url="redis://localhost:6379",
            redis_db=1,
            redis_password="secret",
            pool_min_size=5,
            pool_max_size=20,
            options={"compress": True},
        )
        
        assert config.default_ttl == 7200
        assert config.max_size == 5000
        assert config.prefix == "app:"
        assert config.key_prefix == "cache:"
        assert config.serializer == "pickle"
        assert config.redis_url == "redis://localhost:6379"
        assert config.redis_db == 1
        assert config.redis_password == "secret"
        assert config.pool_min_size == 5
        assert config.pool_max_size == 20
        assert config.options == {"compress": True}

    def test_partial_custom_values(self) -> None:
        """Test partial custom configuration."""
        config = CacheConfig(
            default_ttl=1800,
            prefix="test:",
        )
        
        assert config.default_ttl == 1800
        assert config.prefix == "test:"
        assert config.max_size == 10000  # default
        assert config.serializer == "json"  # default

    def test_options_isolation(self) -> None:
        """Test that options dict is isolated between instances."""
        config1 = CacheConfig()
        config2 = CacheConfig()
        
        config1.options["key1"] = "value1"
        
        assert "key1" not in config2.options
