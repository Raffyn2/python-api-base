"""Unit tests for JWT models.

Tests TokenPayload and TokenPair dataclasses.
"""

from datetime import UTC, datetime, timedelta

import pytest

from infrastructure.auth.jwt.models import TokenPair, TokenPayload


class TestTokenPayload:
    """Tests for TokenPayload dataclass."""

    def test_creation(self) -> None:
        """Test TokenPayload creation."""
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)
        
        payload = TokenPayload(
            sub="user123",
            exp=exp,
            iat=now,
            jti="token-id-123",
        )
        
        assert payload.sub == "user123"
        assert payload.exp == exp
        assert payload.iat == now
        assert payload.jti == "token-id-123"
        assert payload.scopes == ()
        assert payload.token_type == "access"

    def test_creation_with_scopes(self) -> None:
        """Test TokenPayload with scopes."""
        now = datetime.now(UTC)
        
        payload = TokenPayload(
            sub="user123",
            exp=now + timedelta(hours=1),
            iat=now,
            jti="token-id",
            scopes=("read", "write", "admin"),
        )
        
        assert payload.scopes == ("read", "write", "admin")

    def test_creation_refresh_token(self) -> None:
        """Test TokenPayload for refresh token."""
        now = datetime.now(UTC)
        
        payload = TokenPayload(
            sub="user123",
            exp=now + timedelta(days=7),
            iat=now,
            jti="refresh-token-id",
            token_type="refresh",
        )
        
        assert payload.token_type == "refresh"

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)
        
        payload = TokenPayload(
            sub="user123",
            exp=exp,
            iat=now,
            jti="token-id",
            scopes=("read", "write"),
            token_type="access",
        )
        
        result = payload.to_dict()
        
        assert result["sub"] == "user123"
        assert result["exp"] == int(exp.timestamp())
        assert result["iat"] == int(now.timestamp())
        assert result["jti"] == "token-id"
        assert result["scopes"] == ["read", "write"]
        assert result["token_type"] == "access"

    def test_from_dict(self) -> None:
        """Test from_dict creation."""
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)
        
        data = {
            "sub": "user456",
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "jti": "token-xyz",
            "scopes": ["admin"],
            "token_type": "access",
        }
        
        payload = TokenPayload.from_dict(data)
        
        assert payload.sub == "user456"
        assert payload.jti == "token-xyz"
        assert payload.scopes == ("admin",)
        assert payload.token_type == "access"

    def test_from_dict_defaults(self) -> None:
        """Test from_dict with missing optional fields."""
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)
        
        data = {
            "sub": "user789",
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "jti": "token-abc",
        }
        
        payload = TokenPayload.from_dict(data)
        
        assert payload.scopes == ()
        assert payload.token_type == "access"

    def test_round_trip(self) -> None:
        """Test to_dict then from_dict preserves data."""
        now = datetime.now(UTC)
        exp = now + timedelta(hours=1)
        
        original = TokenPayload(
            sub="user123",
            exp=exp,
            iat=now,
            jti="token-id",
            scopes=("read", "write"),
            token_type="access",
        )
        
        data = original.to_dict()
        restored = TokenPayload.from_dict(data)
        
        assert restored.sub == original.sub
        assert restored.jti == original.jti
        assert restored.scopes == original.scopes
        assert restored.token_type == original.token_type

    def test_pretty_print(self) -> None:
        """Test pretty_print formatting."""
        now = datetime.now(UTC)
        
        payload = TokenPayload(
            sub="user123",
            exp=now + timedelta(hours=1),
            iat=now,
            jti="token-id",
            scopes=("read",),
        )
        
        result = payload.pretty_print()
        
        assert "TokenPayload" in result
        assert "user123" in result
        assert "token-id" in result
        assert "read" in result

    def test_immutability(self) -> None:
        """Test TokenPayload is immutable."""
        now = datetime.now(UTC)
        
        payload = TokenPayload(
            sub="user123",
            exp=now + timedelta(hours=1),
            iat=now,
            jti="token-id",
        )
        
        with pytest.raises(AttributeError):
            payload.sub = "other"  # type: ignore


class TestTokenPair:
    """Tests for TokenPair dataclass."""

    def test_creation(self) -> None:
        """Test TokenPair creation."""
        pair = TokenPair(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
        )
        
        assert pair.access_token == "access.token.here"
        assert pair.refresh_token == "refresh.token.here"
        assert pair.token_type == "bearer"
        assert pair.expires_in == 1800

    def test_creation_custom_values(self) -> None:
        """Test TokenPair with custom values."""
        pair = TokenPair(
            access_token="access",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=3600,
        )
        
        assert pair.token_type == "Bearer"
        assert pair.expires_in == 3600

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        pair = TokenPair(
            access_token="access.token",
            refresh_token="refresh.token",
            token_type="bearer",
            expires_in=1800,
        )
        
        result = pair.to_dict()
        
        assert result["access_token"] == "access.token"
        assert result["refresh_token"] == "refresh.token"
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 1800

    def test_immutability(self) -> None:
        """Test TokenPair is immutable."""
        pair = TokenPair(
            access_token="access",
            refresh_token="refresh",
        )
        
        with pytest.raises(AttributeError):
            pair.access_token = "new"  # type: ignore
