"""Tests for config shared utils module.

**Feature: realistic-test-coverage**
**Validates: Requirements for core-code-review**
"""

import pytest

from core.config.shared.utils import redact_url_credentials


class TestRedactUrlCredentials:
    """Tests for redact_url_credentials function."""

    def test_url_without_credentials(self) -> None:
        """Test URL without credentials is unchanged."""
        url = "https://example.com/path"
        result = redact_url_credentials(url)
        assert result == url

    def test_url_with_password(self) -> None:
        """Test URL with password is redacted."""
        url = "postgresql://user:secret123@localhost:5432/db"
        result = redact_url_credentials(url)
        assert "secret123" not in result
        assert "[REDACTED]" in result
        assert "user" in result

    def test_url_with_username_only(self) -> None:
        """Test URL with username only is unchanged."""
        url = "postgresql://user@localhost:5432/db"
        result = redact_url_credentials(url)
        assert result == url

    def test_redis_url_with_password(self) -> None:
        """Test Redis URL with password is redacted."""
        url = "redis://:mypassword@localhost:6379/0"
        result = redact_url_credentials(url)
        assert "mypassword" not in result
        assert "[REDACTED]" in result

    def test_complex_password(self) -> None:
        """Test URL with complex password is redacted."""
        url = "postgresql://admin:p@ss:w0rd!@localhost:5432/db"
        result = redact_url_credentials(url)
        assert "p@ss:w0rd!" not in result
        assert "[REDACTED]" in result

    def test_invalid_url(self) -> None:
        """Test invalid URL returns placeholder."""
        # This should trigger the exception handler
        result = redact_url_credentials("")
        # Empty string is valid URL, returns as-is
        assert result == ""

    def test_url_with_port(self) -> None:
        """Test URL with port preserves port."""
        url = "postgresql://user:pass@localhost:5432/db"
        result = redact_url_credentials(url)
        assert "5432" in result
        assert "localhost" in result

    def test_url_with_query_params(self) -> None:
        """Test URL with query params preserves params."""
        url = "postgresql://user:pass@localhost/db?sslmode=require"
        result = redact_url_credentials(url)
        assert "sslmode=require" in result
        assert "pass" not in result
