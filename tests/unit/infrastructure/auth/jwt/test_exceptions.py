"""Unit tests for JWT exceptions.

Tests InvalidKeyError and AlgorithmMismatchError.
"""

import pytest

from infrastructure.auth.jwt.exceptions import (
    AlgorithmMismatchError,
    InvalidKeyError,
)


class TestInvalidKeyError:
    """Tests for InvalidKeyError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = InvalidKeyError()

        assert str(error) == "Invalid key format"
        assert error.message == "Invalid key format"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = InvalidKeyError("Key must be at least 32 characters")

        assert str(error) == "Key must be at least 32 characters"
        assert error.message == "Key must be at least 32 characters"

    def test_is_exception(self) -> None:
        """Test error is an exception."""
        error = InvalidKeyError()

        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(InvalidKeyError) as exc_info:
            raise InvalidKeyError("Test error")

        assert exc_info.value.message == "Test error"


class TestAlgorithmMismatchError:
    """Tests for AlgorithmMismatchError."""

    def test_message_format(self) -> None:
        """Test error message format."""
        error = AlgorithmMismatchError(expected="RS256", received="HS256")

        assert "RS256" in str(error)
        assert "HS256" in str(error)
        assert "mismatch" in str(error).lower()

    def test_attributes(self) -> None:
        """Test error attributes."""
        error = AlgorithmMismatchError(expected="ES256", received="RS256")

        assert error.expected == "ES256"
        assert error.received == "RS256"

    def test_is_exception(self) -> None:
        """Test error is an exception."""
        error = AlgorithmMismatchError(expected="RS256", received="HS256")

        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(AlgorithmMismatchError) as exc_info:
            raise AlgorithmMismatchError(expected="RS256", received="HS256")

        assert exc_info.value.expected == "RS256"
        assert exc_info.value.received == "HS256"
