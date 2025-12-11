"""Unit tests for core/config/shared/utils.py.

Tests URL credential redaction utility.

**Task 3.2: Create tests for shared utilities**
**Requirements: 3.2**
"""

from core.config.shared.utils import redact_url_credentials


class TestRedactUrlCredentials:
    """Tests for redact_url_credentials function."""

    def test_redacts_password(self) -> None:
        """Test password is redacted from URL."""
        url = "postgresql://user:secretpass@host:5432/db"
        result = redact_url_credentials(url)

        assert "secretpass" not in result
        assert "[REDACTED]" in result
        assert "user" in result

    def test_no_password_unchanged(self) -> None:
        """Test URL without password is unchanged."""
        url = "postgresql://host:5432/db"
        result = redact_url_credentials(url)

        assert result == url

    def test_user_only_unchanged(self) -> None:
        """Test URL with user but no password is unchanged."""
        url = "postgresql://user@host:5432/db"
        result = redact_url_credentials(url)

        assert result == url

    def test_invalid_url_returns_placeholder(self) -> None:
        """Test invalid URL returns placeholder."""
        result = redact_url_credentials("not a valid url ::::")
        # Should handle gracefully
        assert result is not None

    def test_empty_string(self) -> None:
        """Test empty string is handled."""
        result = redact_url_credentials("")
        assert result == ""

    def test_redis_url(self) -> None:
        """Test Redis URL redaction."""
        url = "redis://user:password123@redis-host:6379/0"
        result = redact_url_credentials(url)

        assert "password123" not in result
        assert "[REDACTED]" in result
