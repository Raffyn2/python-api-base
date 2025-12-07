"""Unit tests for application settings.

Tests Settings, DatabaseSettings, and get_settings.
"""

import pytest

from core.config import Settings, get_settings
from core.config.infrastructure import DatabaseSettings


class TestDatabaseSettings:
    """Tests for DatabaseSettings."""

    def test_default_values(self) -> None:
        """Test default database settings."""
        settings = DatabaseSettings()
        assert "postgresql" in settings.url
        assert settings.pool_size == 5
        assert settings.max_overflow == 10
        assert settings.echo is False

    def test_custom_values(self) -> None:
        """Test custom database settings."""
        settings = DatabaseSettings(
            url="postgresql://user:pass@host/db",
            pool_size=10,
            max_overflow=20,
            echo=True,
        )
        assert settings.pool_size == 10
        assert settings.max_overflow == 20
        assert settings.echo is True

    def test_get_safe_url_redacts_password(self) -> None:
        """Test get_safe_url redacts credentials."""
        settings = DatabaseSettings(url="postgresql://user:secret@host/db")
        safe_url = settings.get_safe_url()
        assert "secret" not in safe_url
        assert "***" in safe_url or "user" in safe_url

    def test_repr_is_safe(self) -> None:
        """Test __repr__ doesn't expose credentials."""
        settings = DatabaseSettings(url="postgresql://user:secret@host/db")
        repr_str = repr(settings)
        assert "secret" not in repr_str

    def test_pool_size_validation(self) -> None:
        """Test pool_size must be >= 1."""
        with pytest.raises(ValueError):
            DatabaseSettings(pool_size=0)

    def test_pool_size_max_validation(self) -> None:
        """Test pool_size must be <= 100."""
        with pytest.raises(ValueError):
            DatabaseSettings(pool_size=101)


class TestSettings:
    """Tests for main Settings class."""

    def test_default_values(self) -> None:
        """Test default application settings."""
        settings = Settings()
        assert settings.app_name == "My API"
        assert settings.debug is False
        assert settings.version == "0.1.0"
        assert settings.api_prefix == "/api/v1"

    def test_nested_database_settings(self) -> None:
        """Test nested database settings are created."""
        settings = Settings()
        assert settings.database is not None
        assert isinstance(settings.database, DatabaseSettings)

    def test_nested_security_settings(self) -> None:
        """Test nested security settings are created."""
        settings = Settings()
        assert settings.security is not None

    def test_nested_redis_settings(self) -> None:
        """Test nested redis settings are created."""
        settings = Settings()
        assert settings.redis is not None

    def test_nested_observability_settings(self) -> None:
        """Test nested observability settings are created."""
        settings = Settings()
        assert settings.observability is not None


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_settings(self) -> None:
        """Test get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_is_cached(self) -> None:
        """Test get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

