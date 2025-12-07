"""Unit tests for security settings.

Tests SecuritySettings and RedisSettings validation.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from core.config.security import RATE_LIMIT_PATTERN, RedisSettings, SecuritySettings


class TestRateLimitPattern:
    """Tests for rate limit pattern regex."""

    def test_valid_per_second(self) -> None:
        """Test valid per-second rate limit."""
        assert RATE_LIMIT_PATTERN.match("10/second")

    def test_valid_per_minute(self) -> None:
        """Test valid per-minute rate limit."""
        assert RATE_LIMIT_PATTERN.match("100/minute")

    def test_valid_per_hour(self) -> None:
        """Test valid per-hour rate limit."""
        assert RATE_LIMIT_PATTERN.match("1000/hour")

    def test_valid_per_day(self) -> None:
        """Test valid per-day rate limit."""
        assert RATE_LIMIT_PATTERN.match("10000/day")

    def test_invalid_format(self) -> None:
        """Test invalid format is rejected."""
        assert not RATE_LIMIT_PATTERN.match("100")
        assert not RATE_LIMIT_PATTERN.match("100/")
        assert not RATE_LIMIT_PATTERN.match("/minute")
        assert not RATE_LIMIT_PATTERN.match("100/week")


class TestSecuritySettings:
    """Tests for SecuritySettings."""

    def test_valid_settings(self) -> None:
        """Test valid security settings."""
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

    def test_secret_key_too_short(self) -> None:
        """Test secret key validation rejects short keys."""
        with pytest.raises(Exception, match="at least 32"):
            SecuritySettings(secret_key=SecretStr("short"))

    def test_invalid_rate_limit_format(self) -> None:
        """Test invalid rate limit format is rejected."""
        with pytest.raises(ValueError, match="Invalid rate limit format"):
            SecuritySettings(
                secret_key=SecretStr("a" * 32),
                rate_limit="invalid",
            )

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_wildcard_cors_blocked_in_production(self) -> None:
        """Test wildcard CORS is blocked in production."""
        with pytest.raises(ValueError, match="not allowed in production"):
            SecuritySettings(
                secret_key=SecretStr("a" * 32),
                cors_origins=["*"],
            )

    @patch.dict(os.environ, {"ENVIRONMENT": "staging"})
    def test_wildcard_cors_blocked_in_staging(self) -> None:
        """Test wildcard CORS is blocked in staging."""
        with pytest.raises(ValueError, match="not allowed in staging"):
            SecuritySettings(
                secret_key=SecretStr("a" * 32),
                cors_origins=["*"],
            )

    @patch.dict(os.environ, {"ENVIRONMENT": "development"})
    def test_wildcard_cors_allowed_in_development(self) -> None:
        """Test wildcard CORS is allowed in development."""
        settings = SecuritySettings(
            secret_key=SecretStr("a" * 32),
            cors_origins=["*"],
        )
        assert "*" in settings.cors_origins

    def test_csp_default(self) -> None:
        """Test default CSP value."""
        settings = SecuritySettings(secret_key=SecretStr("a" * 32))
        assert settings.csp == "default-src 'self'"

    def test_permissions_policy_default(self) -> None:
        """Test default permissions policy."""
        settings = SecuritySettings(secret_key=SecretStr("a" * 32))
        assert "geolocation=()" in settings.permissions_policy


class TestRedisSettings:
    """Tests for RedisSettings."""

    def test_default_values(self) -> None:
        """Test default Redis settings."""
        settings = RedisSettings()
        assert settings.url == "redis://localhost:6379/0"
        assert settings.enabled is False
        assert settings.token_ttl == 604800

    def test_custom_values(self) -> None:
        """Test custom Redis settings."""
        settings = RedisSettings(
            url="redis://redis:6379/1",
            enabled=True,
            token_ttl=3600,
        )
        assert settings.url == "redis://redis:6379/1"
        assert settings.enabled is True
        assert settings.token_ttl == 3600

    def test_token_ttl_minimum(self) -> None:
        """Test token TTL minimum validation."""
        with pytest.raises(ValueError):
            RedisSettings(token_ttl=30)  # Below minimum of 60
