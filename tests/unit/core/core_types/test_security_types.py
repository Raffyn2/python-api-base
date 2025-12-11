"""Unit tests for security type definitions.

Tests Password, SecurePassword, and JWTToken type aliases.
"""

import pytest
from pydantic import BaseModel, ValidationError

from core.types.domain.security_types import JWTToken, Password


class PasswordModel(BaseModel):
    """Model with Password field."""

    password: Password


class JWTTokenModel(BaseModel):
    """Model with JWTToken field."""

    token: JWTToken


class TestPassword:
    """Tests for Password type."""

    def test_valid_password(self) -> None:
        """Test valid password is accepted."""
        model = PasswordModel(password="password123")
        assert model.password == "password123"

    def test_valid_password_min_length(self) -> None:
        """Test password at minimum length is accepted."""
        model = PasswordModel(password="12345678")
        assert model.password == "12345678"

    def test_invalid_password_too_short(self) -> None:
        """Test password too short is rejected."""
        with pytest.raises(ValidationError):
            PasswordModel(password="1234567")

    def test_invalid_password_too_long(self) -> None:
        """Test password too long is rejected."""
        with pytest.raises(ValidationError):
            PasswordModel(password="a" * 129)

    def test_valid_password_max_length(self) -> None:
        """Test password at maximum length is accepted."""
        model = PasswordModel(password="a" * 128)
        assert len(model.password) == 128


class TestJWTToken:
    """Tests for JWTToken type."""

    def test_valid_jwt_token(self) -> None:
        """Test valid JWT token is accepted."""
        # Minimal valid JWT format
        token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        model = JWTTokenModel(token=token)
        assert model.token == token

    def test_valid_jwt_token_simple(self) -> None:
        """Test simple valid JWT format is accepted."""
        token = "header_part_here.payload_part_here.signature_part"
        model = JWTTokenModel(token=token)
        assert model.token == token

    def test_invalid_jwt_token_no_dots(self) -> None:
        """Test JWT without dots is rejected."""
        with pytest.raises(ValidationError):
            JWTTokenModel(token="invalidtokenwithoutdots")

    def test_invalid_jwt_token_one_dot(self) -> None:
        """Test JWT with only one dot is rejected."""
        with pytest.raises(ValidationError):
            JWTTokenModel(token="header.payload")

    def test_invalid_jwt_token_too_short(self) -> None:
        """Test JWT too short is rejected."""
        with pytest.raises(ValidationError):
            JWTTokenModel(token="a.b.c")

    def test_invalid_jwt_token_invalid_chars(self) -> None:
        """Test JWT with invalid characters is rejected."""
        with pytest.raises(ValidationError):
            JWTTokenModel(token="header with spaces.payload.signature")
