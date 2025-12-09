"""Unit tests for core/config/application/settings.py.

Tests configuration loading, defaults, and validation.

**Task 3.1: Create tests for settings.py**
**Requirements: 3.2**
"""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from core.config.application.settings import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        with patch.dict(os.environ, {"SECURITY__SECRET_KEY": "a" * 32}, clear=False):
            settings = Settings()

            assert settings.app_name == "My API"
            assert settings.debug is False
            assert settings.version == "0.1.0"
            assert settings.api_prefix == "/api/v1"

    def test_nested_database_settings_defaults(self) -> None:
        """Test database settings have correct defaults."""
        with patch.dict(os.environ, {"SECURITY__SECRET_KEY": "a" * 32}, clear=False):
            settings = Settings()

            assert settings.database.pool_size == 5
            assert settings.database.max_overflow == 10
            assert settings.database.echo is False
            assert "postgresql" in settings.database.url

    def test_nested_security_settings_structure(self) -> None:
        """Test security settings have correct structure."""
        with patch.dict(os.environ, {"SECURITY__SECRET_KEY": "a" * 32}, clear=False):
            settings = Settings()

            # Verify security settings exist and have expected types
            assert hasattr(settings, "security")
            assert isinstance(settings.security.cors_origins, list)
            assert isinstance(settings.security.algorithm, str)
            assert isinstance(settings.security.access_token_expire_minutes, int)

    def test_nested_redis_settings_defaults(self) -> None:
        """Test Redis settings have correct defaults."""
        with patch.dict(os.environ, {"SECURITY__SECRET_KEY": "a" * 32}, clear=False):
            settings = Settings()

            assert settings.redis.enabled is False
            assert settings.redis.token_ttl == 604800
            assert "redis://" in settings.redis.url

    def test_nested_observability_settings_defaults(self) -> None:
        """Test observability settings have correct defaults."""
        with patch.dict(os.environ, {"SECURITY__SECRET_KEY": "a" * 32}, clear=False):
            settings = Settings()

            assert settings.observability.log_level == "INFO"
            assert settings.observability.log_format == "json"
            assert settings.observability.enable_tracing is True
            assert settings.observability.enable_metrics is True

    def test_env_override(self) -> None:
        """Test environment variables override defaults."""
        env_vars = {
            "APP_NAME": "Test API",
            "DEBUG": "true",
            "VERSION": "2.0.0",
            "API_PREFIX": "/api/v2",
            "SECURITY__SECRET_KEY": "a" * 32,
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()

            assert settings.app_name == "Test API"
            assert settings.debug is True
            assert settings.version == "2.0.0"
            assert settings.api_prefix == "/api/v2"

    def test_nested_env_override(self) -> None:
        """Test nested environment variables override defaults."""
        env_vars = {
            "DATABASE__POOL_SIZE": "20",
            "DATABASE__ECHO": "true",
            "SECURITY__SECRET_KEY": "b" * 32,
            "SECURITY__RATE_LIMIT": "200/minute",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()

            assert settings.database.pool_size == 20
            assert settings.database.echo is True
            assert settings.security.rate_limit == "200/minute"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_settings_instance(self) -> None:
        """Test get_settings returns a Settings instance."""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"SECURITY__SECRET_KEY": "a" * 32}, clear=False):
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_caching(self) -> None:
        """Test get_settings returns cached instance."""
        get_settings.cache_clear()
        with patch.dict(os.environ, {"SECURITY__SECRET_KEY": "a" * 32}, clear=False):
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2
