"""Tests for JWT providers module.

**Feature: realistic-test-coverage**
**Validates: Requirements 1.1, 1.2, 1.4**
"""

import pytest

from infrastructure.auth.jwt.exceptions import InvalidKeyError
from infrastructure.auth.jwt.hs256_provider import HS256Provider


class TestHS256Provider:
    """Tests for HS256Provider."""

    def test_create_provider(self) -> None:
        """Test creating HS256 provider."""
        provider = HS256Provider(secret_key="a" * 32)
        assert provider.algorithm == "HS256"

    def test_secret_key_too_short(self) -> None:
        """Test secret key validation."""
        with pytest.raises(InvalidKeyError, match="32 characters"):
            HS256Provider(secret_key="short")

    def test_empty_secret_key(self) -> None:
        """Test empty secret key fails."""
        with pytest.raises(InvalidKeyError):
            HS256Provider(secret_key="")

    def test_sign_and_verify(self) -> None:
        """Test signing and verifying token."""
        provider = HS256Provider(secret_key="a" * 32)
        token = provider.sign({"sub": "user-123", "role": "admin"})
        
        assert token is not None
        assert isinstance(token, str)
        
        claims = provider.verify(token)
        assert claims["sub"] == "user-123"
        assert claims["role"] == "admin"

    def test_sign_with_issuer(self) -> None:
        """Test signing with issuer."""
        provider = HS256Provider(
            secret_key="a" * 32,
            issuer="test-issuer",
        )
        token = provider.sign({"sub": "user-123"})
        claims = provider.verify(token)
        
        assert claims["iss"] == "test-issuer"

    def test_sign_with_audience(self) -> None:
        """Test signing with audience."""
        provider = HS256Provider(
            secret_key="a" * 32,
            audience="test-audience",
        )
        token = provider.sign({"sub": "user-123"})
        claims = provider.verify(token)
        
        assert claims["aud"] == "test-audience"

    def test_get_signing_key(self) -> None:
        """Test getting signing key."""
        provider = HS256Provider(secret_key="a" * 32)
        key = provider._get_signing_key()
        assert key == "a" * 32

    def test_get_verification_key(self) -> None:
        """Test getting verification key."""
        provider = HS256Provider(secret_key="a" * 32)
        key = provider._get_verification_key()
        assert key == "a" * 32

    def test_signing_and_verification_keys_same(self) -> None:
        """Test signing and verification keys are the same (symmetric)."""
        provider = HS256Provider(secret_key="a" * 32)
        assert provider._get_signing_key() == provider._get_verification_key()

    def test_production_mode_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test production mode logs warning."""
        import logging
        
        with caplog.at_level(logging.WARNING):
            HS256Provider(secret_key="a" * 32, production_mode=True)
        
        assert "SECURITY WARNING" in caplog.text or "HS256" in caplog.text
