"""Tests for security config module.

**Feature: realistic-test-coverage**
**Validates: Requirements 1.1, 1.2, 1.4**
"""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from core.config.security.security import (
    RATE_LIMIT_PATTERN,
    RedisSettings,
    SecuritySettings,
)


class TestRateLimitPattern:
    """Tests for RATE_LIMIT_PATTERN regex."""

    def test_valid_per_second(self) -> None:
        """Test valid per second format."""
        assert RATE_LIMIT_PATTERN.match("10/second")

    def test_valid_per_minute(self) -> None:
        """Test valid per minute format."""
        assert RATE_LIMIT_PATTERN.match("100/minute")

    def test_valid_per_hour(self) -> None:
        """Test valid per hour format."""
        assert RATE_LIMIT_PATTERN.match("1000/hour")

    def test_valid_per_day(self) -> None:
        """Test valid per day format."""
        assert RATE_LIMIT_PATTERN.match("10000/day")

    def test_invalid_format(self) -> None:
        """Test invalid format."""
        assert not RATE_LIMIT_PATTERN.match("100")
        assert not RATE_LIMIT_PATTERN.match("100/week")
        assert not RATE_LIMIT_PATTERN.match("abc/minute")


class TestSecuritySettings:
    """Tests for SecuritySettings."""

    def test_valid_settings(self) -> None:
        """Test creating valid security settings."""
        settings = SecuritySettings(
            secret_key=SecretStr("a" * 32),
            cors_origins=["http://localhost:3000"],
            rate_limit="100/minute",
        )
        assert settings.secret_key.get_secret_value() == "a" * 32
        assert settings.cors_origins == ["http://localhost:3000"]
        assert settings.rate_limit == "100/minute"

    def test_default_values(self) -> None:
        """Test default values."""
        settings = SecuritySettings(secret_key=SecretStr("a" * 32))
        assert settings.cors_origins == ["*"]
        assert settings.rate_limit == "100/minute"
        assert settings.algorithm == "RS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.csp == "default-src 'self'"

    def test_secret_key_too_short(self) -> None:
        """Test secret key validation fails for short keys."""
        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings(secret_key=SecretStr("short"))
        error_str = str(exc_info.value).lower()
        assert "32" in error_str or "too_short" in error_str

    def test_invalid_rate_limit_format(self) -> None:
        """Test invalid rate limit format."""
        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings(
                secret_key=SecretStr("a" * 32),
                rate_limit="invalid",
            )
        assert "rate limit" in str(exc_info.value).lower()

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_wildcard_cors_blocked_in_production(self) -> None:
        """Test wildcard CORS is blocked in production."""
        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings(
                secret_key=SecretStr("a" * 32),
                cors_origins=["*"],
            )
        assert "not allowed" in str(exc_info.value).lower()

    @patch.dict(os.environ, {"ENVIRONMENT": "staging"})
    def test_wildcard_cors_blocked_in_staging(self) -> None:
        """Test wildcard CORS is blocked in staging."""
        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings(
                secret_key=SecretStr("a" * 32),
                cors_origins=["*"],
            )
        assert "not allowed" in str(exc_info.value).lower()

    @patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
    def test_wildcard_cors_allowed_in_development(self) -> None:
        """Test wildcard CORS is allowed in development."""
        settings = SecuritySettings(
            secret_key=SecretStr("a" * 32),
            cors_origins=["*"],
        )
        assert "*" in settings.cors_origins

    def test_access_token_expire_minutes_minimum(self) -> None:
        """Test access token expire minutes minimum."""
        with pytest.raises(ValidationError):
            SecuritySettings(
                secret_key=SecretStr("a" * 32),
                access_token_expire_minutes=0,
            )


class TestRedisSettings:
    """Tests for RedisSettings."""

    def test_default_values(self) -> None:
        """Test default values."""
        settings = RedisSettings()
        assert settings.url == "redis://localhost:6379/0"
        assert settings.enabled is False
        assert settings.token_ttl == 604800

    def test_custom_values(self) -> None:
        """Test custom values."""
        settings = RedisSettings(
            url="redis://redis.example.com:6379/1",
            enabled=True,
            token_ttl=3600,
        )
        assert settings.url == "redis://redis.example.com:6379/1"
        assert settings.enabled is True
        assert settings.token_ttl == 3600

    def test_token_ttl_minimum(self) -> None:
        """Test token TTL minimum validation."""
        with pytest.raises(ValidationError):
            RedisSettings(token_ttl=30)  # Below minimum of 60
