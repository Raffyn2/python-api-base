"""Unit tests for JWT configuration.

Tests JWTKeyConfig dataclass and validation.
"""

import pytest

from infrastructure.auth.jwt.config import JWTKeyConfig
from infrastructure.auth.jwt.exceptions import InvalidKeyError


class TestJWTKeyConfig:
    """Tests for JWTKeyConfig dataclass."""

    def test_hs256_valid(self) -> None:
        """Test valid HS256 configuration."""
        config = JWTKeyConfig(
            algorithm="HS256",
            secret_key="my-secret-key-at-least-32-chars-long",
        )

        assert config.algorithm == "HS256"
        assert config.secret_key == "my-secret-key-at-least-32-chars-long"
        assert config.private_key is None
        assert config.public_key is None

    def test_hs256_missing_secret(self) -> None:
        """Test HS256 without secret key raises error."""
        with pytest.raises(InvalidKeyError, match="HS256 requires secret_key"):
            JWTKeyConfig(algorithm="HS256")

    def test_rs256_with_private_key(self) -> None:
        """Test RS256 with private key only."""
        private_key = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"

        config = JWTKeyConfig(
            algorithm="RS256",
            private_key=private_key,
        )

        assert config.algorithm == "RS256"
        assert config.private_key == private_key
        assert config.public_key is None

    def test_rs256_with_public_key(self) -> None:
        """Test RS256 with public key only."""
        public_key = "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----"

        config = JWTKeyConfig(
            algorithm="RS256",
            public_key=public_key,
        )

        assert config.algorithm == "RS256"
        assert config.public_key == public_key
        assert config.private_key is None

    def test_rs256_with_both_keys(self) -> None:
        """Test RS256 with both keys."""
        private_key = "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"
        public_key = "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----"

        config = JWTKeyConfig(
            algorithm="RS256",
            private_key=private_key,
            public_key=public_key,
        )

        assert config.private_key == private_key
        assert config.public_key == public_key

    def test_rs256_missing_keys(self) -> None:
        """Test RS256 without any keys raises error."""
        with pytest.raises(InvalidKeyError, match="RS256 requires"):
            JWTKeyConfig(algorithm="RS256")

    def test_es256_with_private_key(self) -> None:
        """Test ES256 with private key."""
        private_key = "-----BEGIN EC PRIVATE KEY-----\ntest\n-----END EC PRIVATE KEY-----"

        config = JWTKeyConfig(
            algorithm="ES256",
            private_key=private_key,
        )

        assert config.algorithm == "ES256"
        assert config.private_key == private_key

    def test_es256_missing_keys(self) -> None:
        """Test ES256 without any keys raises error."""
        with pytest.raises(InvalidKeyError, match="ES256 requires"):
            JWTKeyConfig(algorithm="ES256")

    def test_unsupported_algorithm(self) -> None:
        """Test unsupported algorithm raises error."""
        with pytest.raises(InvalidKeyError, match="Unsupported algorithm"):
            JWTKeyConfig(algorithm="INVALID")

    def test_immutability(self) -> None:
        """Test JWTKeyConfig is immutable."""
        config = JWTKeyConfig(
            algorithm="HS256",
            secret_key="secret",
        )

        with pytest.raises(AttributeError):
            config.algorithm = "RS256"  # type: ignore
