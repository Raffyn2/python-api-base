"""Unit tests for JWT errors.

Tests TokenExpiredError, TokenInvalidError, TokenRevokedError.
"""

import pytest

from infrastructure.auth.jwt.errors import (
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
)


class TestTokenExpiredError:
    """Tests for TokenExpiredError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = TokenExpiredError()
        
        assert str(error) == "Token has expired"
        assert error.error_code == "TOKEN_EXPIRED"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = TokenExpiredError("Custom expiration message")
        
        assert str(error) == "Custom expiration message"
        assert error.error_code == "TOKEN_EXPIRED"

    def test_is_exception(self) -> None:
        """Test error is an exception."""
        error = TokenExpiredError()
        
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(TokenExpiredError) as exc_info:
            raise TokenExpiredError("Test")
        
        assert exc_info.value.error_code == "TOKEN_EXPIRED"


class TestTokenInvalidError:
    """Tests for TokenInvalidError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = TokenInvalidError()
        
        assert str(error) == "Invalid token"
        assert error.error_code == "TOKEN_INVALID"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = TokenInvalidError("Token format is wrong")
        
        assert str(error) == "Token format is wrong"
        assert error.error_code == "TOKEN_INVALID"

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(TokenInvalidError) as exc_info:
            raise TokenInvalidError()
        
        assert exc_info.value.error_code == "TOKEN_INVALID"


class TestTokenRevokedError:
    """Tests for TokenRevokedError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = TokenRevokedError()
        
        assert str(error) == "Token has been revoked"
        assert error.error_code == "TOKEN_REVOKED"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = TokenRevokedError("Token was revoked by admin")
        
        assert str(error) == "Token was revoked by admin"
        assert error.error_code == "TOKEN_REVOKED"

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(TokenRevokedError) as exc_info:
            raise TokenRevokedError()
        
        assert exc_info.value.error_code == "TOKEN_REVOKED"
