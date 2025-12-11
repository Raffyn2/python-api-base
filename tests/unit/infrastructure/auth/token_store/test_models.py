"""Tests for token store models module.

**Feature: realistic-test-coverage**
**Validates: Requirements 3.1, 5.1, 5.2, 5.3**
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.auth.token_store.models import StoredToken


class TestStoredToken:
    """Tests for StoredToken dataclass."""

    def test_create_token(self) -> None:
        """Test creating stored token."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
        )
        assert token.jti == "token-123"
        assert token.user_id == "user-456"
        assert token.revoked is False

    def test_is_expired_false(self) -> None:
        """Test is_expired returns False for valid token."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
        )
        assert token.is_expired() is False

    def test_is_expired_true(self) -> None:
        """Test is_expired returns True for expired token."""
        now = datetime.now(UTC)
        expires = now - timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now - timedelta(hours=2),
            expires_at=expires,
        )
        assert token.is_expired() is True

    def test_is_valid_true(self) -> None:
        """Test is_valid returns True for valid token."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
            revoked=False,
        )
        assert token.is_valid() is True

    def test_is_valid_false_when_revoked(self) -> None:
        """Test is_valid returns False when revoked."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
            revoked=True,
        )
        assert token.is_valid() is False

    def test_is_valid_false_when_expired(self) -> None:
        """Test is_valid returns False when expired."""
        now = datetime.now(UTC)
        expires = now - timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now - timedelta(hours=2),
            expires_at=expires,
            revoked=False,
        )
        assert token.is_valid() is False

    def test_to_dict(self) -> None:
        """Test converting token to dictionary."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
            revoked=True,
        )
        data = token.to_dict()

        assert data["jti"] == "token-123"
        assert data["user_id"] == "user-456"
        assert data["revoked"] is True
        assert "created_at" in data
        assert "expires_at" in data

    def test_from_dict(self) -> None:
        """Test creating token from dictionary."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        data = {
            "jti": "token-123",
            "user_id": "user-456",
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "revoked": True,
        }
        token = StoredToken.from_dict(data)

        assert token.jti == "token-123"
        assert token.user_id == "user-456"
        assert token.revoked is True

    def test_from_dict_default_revoked(self) -> None:
        """Test from_dict defaults revoked to False."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        data = {
            "jti": "token-123",
            "user_id": "user-456",
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }
        token = StoredToken.from_dict(data)
        assert token.revoked is False

    def test_is_frozen(self) -> None:
        """Test token is immutable."""
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)
        token = StoredToken(
            jti="token-123",
            user_id="user-456",
            created_at=now,
            expires_at=expires,
        )
        with pytest.raises(AttributeError):
            token.jti = "new-jti"
