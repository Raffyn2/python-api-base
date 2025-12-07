"""Tests for Redis configuration.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

import pytest

from infrastructure.redis.config import RedisConfig


class TestRedisConfig:
    """Tests for RedisConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RedisConfig()
        assert config.url is None
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.ssl is False
        assert config.pool_min_size == 1
        assert config.pool_max_size == 10
        assert config.connect_timeout == 5.0
        assert config.socket_timeout == 5.0
        assert config.retry_on_timeout is True
        assert config.key_prefix == ""
        assert config.default_ttl == 3600
        assert config.enable_fallback is True
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_timeout == 30.0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            ssl=True,
            pool_max_size=20,
            default_ttl=7200,
        )
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "secret"
        assert config.ssl is True
        assert config.pool_max_size == 20
        assert config.default_ttl == 7200

    def test_get_url_with_explicit_url(self) -> None:
        """Test get_url returns explicit URL when provided."""
        config = RedisConfig(url="redis://custom:6379/0")
        assert config.get_url() == "redis://custom:6379/0"

    def test_get_url_builds_from_components(self) -> None:
        """Test get_url builds URL from components."""
        config = RedisConfig(host="myhost", port=6380, db=2)
        assert config.get_url() == "redis://myhost:6380/2"

    def test_get_url_with_password(self) -> None:
        """Test get_url includes password in URL."""
        config = RedisConfig(host="myhost", password="secret123")
        url = config.get_url()
        assert url == "redis://:secret123@myhost:6379/0"

    def test_get_url_with_ssl(self) -> None:
        """Test get_url uses rediss scheme for SSL."""
        config = RedisConfig(host="secure.redis.com", ssl=True)
        url = config.get_url()
        assert url.startswith("rediss://")

    def test_get_url_with_ssl_and_password(self) -> None:
        """Test get_url with both SSL and password."""
        config = RedisConfig(
            host="secure.redis.com",
            password="secret",
            ssl=True,
            db=5,
        )
        url = config.get_url()
        assert url == "rediss://:secret@secure.redis.com:6379/5"

    def test_to_connection_kwargs(self) -> None:
        """Test to_connection_kwargs returns correct dict."""
        config = RedisConfig(
            connect_timeout=10.0,
            socket_timeout=15.0,
            retry_on_timeout=False,
            pool_max_size=25,
        )
        kwargs = config.to_connection_kwargs()
        assert kwargs["socket_connect_timeout"] == 10.0
        assert kwargs["socket_timeout"] == 15.0
        assert kwargs["retry_on_timeout"] is False
        assert kwargs["max_connections"] == 25

    def test_to_connection_kwargs_default_values(self) -> None:
        """Test to_connection_kwargs with default values."""
        config = RedisConfig()
        kwargs = config.to_connection_kwargs()
        assert kwargs["socket_connect_timeout"] == 5.0
        assert kwargs["socket_timeout"] == 5.0
        assert kwargs["retry_on_timeout"] is True
        assert kwargs["max_connections"] == 10

    def test_key_prefix_configuration(self) -> None:
        """Test key prefix configuration."""
        config = RedisConfig(key_prefix="myapp:")
        assert config.key_prefix == "myapp:"

    def test_circuit_breaker_configuration(self) -> None:
        """Test circuit breaker configuration."""
        config = RedisConfig(
            circuit_breaker_threshold=10,
            circuit_breaker_timeout=60.0,
        )
        assert config.circuit_breaker_threshold == 10
        assert config.circuit_breaker_timeout == 60.0
