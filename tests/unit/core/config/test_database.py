"""Unit tests for core/config/infrastructure/database.py.

Tests database URL parsing and connection settings.

**Task 3.3: Create tests for database.py configuration**
**Requirements: 3.2**
"""

import pytest

from core.config.infrastructure.database import DatabaseSettings


class TestDatabaseSettings:
    """Tests for DatabaseSettings class."""

    def test_default_values(self) -> None:
        """Test default database settings."""
        settings = DatabaseSettings()

        assert "postgresql+asyncpg" in settings.url
        assert settings.pool_size == 5
        assert settings.max_overflow == 10
        assert settings.echo is False

    def test_custom_url(self) -> None:
        """Test custom database URL."""
        settings = DatabaseSettings(url="postgresql+asyncpg://user:pass@host:5432/db")

        assert settings.url == "postgresql+asyncpg://user:pass@host:5432/db"

    def test_pool_size_validation_min(self) -> None:
        """Test pool_size minimum validation."""
        with pytest.raises(ValueError):
            DatabaseSettings(pool_size=0)

    def test_pool_size_validation_max(self) -> None:
        """Test pool_size maximum validation."""
        with pytest.raises(ValueError):
            DatabaseSettings(pool_size=101)

    def test_pool_size_valid_range(self) -> None:
        """Test pool_size within valid range."""
        settings = DatabaseSettings(pool_size=50)
        assert settings.pool_size == 50

    def test_max_overflow_validation_min(self) -> None:
        """Test max_overflow minimum validation."""
        with pytest.raises(ValueError):
            DatabaseSettings(max_overflow=-1)

    def test_max_overflow_validation_max(self) -> None:
        """Test max_overflow maximum validation."""
        with pytest.raises(ValueError):
            DatabaseSettings(max_overflow=101)

    def test_max_overflow_valid_range(self) -> None:
        """Test max_overflow within valid range."""
        settings = DatabaseSettings(max_overflow=50)
        assert settings.max_overflow == 50

    def test_echo_enabled(self) -> None:
        """Test echo can be enabled."""
        settings = DatabaseSettings(echo=True)
        assert settings.echo is True


class TestDatabaseSettingsGetSafeUrl:
    """Tests for get_safe_url method."""

    def test_redacts_password(self) -> None:
        """Test password is redacted in safe URL."""
        settings = DatabaseSettings(url="postgresql+asyncpg://user:secretpass@host:5432/db")
        safe_url = settings.get_safe_url()

        assert "secretpass" not in safe_url
        assert "[REDACTED]" in safe_url
        assert "user" in safe_url

    def test_no_password_unchanged(self) -> None:
        """Test URL without password is unchanged."""
        settings = DatabaseSettings(url="postgresql+asyncpg://host:5432/db")
        safe_url = settings.get_safe_url()

        assert safe_url == "postgresql+asyncpg://host:5432/db"

    def test_repr_uses_safe_url(self) -> None:
        """Test __repr__ uses safe URL."""
        settings = DatabaseSettings(url="postgresql+asyncpg://user:secretpass@host:5432/db")
        repr_str = repr(settings)

        assert "secretpass" not in repr_str
        assert "[REDACTED]" in repr_str
        assert "pool_size=5" in repr_str
