"""Unit tests for core/config/security/security.py.

Tests security configuration and validation.

**Task 3.2: Create tests for security configuration**
**Requirements: 3.2, 3.5**
"""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from core.config.security.security import (
    RATE_LIMIT_PATTERN,
    RedisSettings,
    SecuritySettings,
)


class TestRateLimitPattern:
    """Tests for RATE_LIMIT_PATTERN regex."""

    @pytest.mark.parametrize(
        "valid_pattern",
        [
            "100/minute",
            "10/second",
            "1000/hour",
            "50/day",
            "1/second",
            "999999/minute",
        ],
    )
    def test_valid_patterns(self, valid_pattern: str) -> None:
        """Test valid rate limit patterns match."""
        assert RATE_LIMIT_PATTERN.match(valid_pattern) is not None

    @pytest.mark.parametrize(
        "invalid_pattern",
        [
            "100/minutes",
            "100/sec",
            "100",
            "/minute",
            "abc/minute",
            "100/MINUTE",
            "100 / minute",
            "",
        ],
    )
    def test_invalid_patterns(self, invalid_pattern: str) -> None:
        """Test invalid rate limit patterns don't match."""
        assert RATE_LIMIT_PATTERN.match(invalid_pattern) is None


class TestSecuritySettings:
    """Tests for SecuritySettings class."""

    def test_default_values(self) -> None:
        """Test default security settings."""
        settings = SecuritySettings(secret_key=SecretStr("a" * 32))

        assert settings.cors_origins == ["*"]
        assert settings.rate_limit == "100/minute"
        assert settings.algorithm == "RS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.csp == "default-src 'self'"

    def test_secret_key_required(self) -> None:
        """Test secret_key is required."""
        with pytest.raises(ValueError):
            SecuritySettings()

    def test_secret_key_min_length(self) -> None:
        """Test secret_key minimum length validation."""
        with pytest.raises(ValueError):
            SecuritySettings(secret_key=SecretStr("short"))

    def test_secret_key_valid_length(self) -> None:
        """Test secret_key with valid length."""
        settings = SecuritySettings(secret_key=SecretStr("a" * 32))
        assert len(settings.secret_key.get_secret_value()) == 32

    def test_rate_limit_validation_valid(self) -> None:
        """Test valid rate limit format."""
        settings = SecuritySettings(secret_key=SecretStr("a" * 32), rate_limit="200/minute")
        assert settings.rate_limit == "200/minute"

    def test_rate_limit_validation_invalid(self) -> None:
        """Test invalid rate limit format raises error."""
        with pytest.raises(ValueError, match="Invalid rate limit format"):
            SecuritySettings(secret_key=SecretStr("a" * 32), rate_limit="invalid")

    def test_cors_wildcard_warning_in_development(self) -> None:
        """Test wildcard CORS is allowed in development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            settings = SecuritySettings(secret_key=SecretStr("a" * 32), cors_origins=["*"])
            assert "*" in settings.cors_origins

    def test_cors_wildcard_blocked_in_production(self) -> None:
        """Test wildcard CORS is blocked in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            with pytest.raises(ValueError, match="Wildcard CORS origin"):
                SecuritySettings(secret_key=SecretStr("a" * 32), cors_origins=["*"])

    def test_cors_wildcard_blocked_in_staging(self) -> None:
        """Test wildcard CORS is blocked in staging."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}, clear=False):
            with pytest.raises(ValueError, match="Wildcard CORS origin"):
                SecuritySettings(secret_key=SecretStr("a" * 32), cors_origins=["*"])

    def test_cors_explicit_origins_allowed_in_production(self) -> None:
        """Test explicit CORS origins are allowed in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            settings = SecuritySettings(
                secret_key=SecretStr("a" * 32),
                cors_origins=["https://example.com", "https://api.example.com"],
            )
            assert "https://example.com" in settings.cors_origins

    def test_access_token_expire_minutes_min(self) -> None:
        """Test access_token_expire_minutes minimum validation."""
        with pytest.raises(ValueError):
            SecuritySettings(secret_key=SecretStr("a" * 32), access_token_expire_minutes=0)

    def test_custom_csp(self) -> None:
        """Test custom CSP header."""
        settings = SecuritySettings(
            secret_key=SecretStr("a" * 32),
            csp="default-src 'self'; script-src 'self' 'unsafe-inline'",
        )
        assert "script-src" in settings.csp


class TestRedisSettings:
    """Tests for RedisSettings class."""

    def test_default_values(self) -> None:
        """Test default Redis settings."""
        settings = RedisSettings()

        assert settings.url == "redis://localhost:6379/0"
        assert settings.enabled is False
        assert settings.token_ttl == 604800

    def test_custom_url(self) -> None:
        """Test custom Redis URL."""
        settings = RedisSettings(url="redis://redis-host:6380/1")
        assert settings.url == "redis://redis-host:6380/1"

    def test_enabled_flag(self) -> None:
        """Test enabled flag."""
        settings = RedisSettings(enabled=True)
        assert settings.enabled is True

    def test_token_ttl_min_validation(self) -> None:
        """Test token_ttl minimum validation."""
        with pytest.raises(ValueError):
            RedisSettings(token_ttl=59)

    def test_token_ttl_valid(self) -> None:
        """Test valid token_ttl."""
        settings = RedisSettings(token_ttl=3600)
        assert settings.token_ttl == 3600
