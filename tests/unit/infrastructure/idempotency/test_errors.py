"""Unit tests for idempotency errors.

Tests IdempotencyKeyConflictError and IdempotencyKeyMissingError.
"""

import pytest

from infrastructure.idempotency import (
    IdempotencyKeyConflictError,
    IdempotencyKeyMissingError,
)


class TestIdempotencyKeyConflictError:
    """Tests for IdempotencyKeyConflictError."""

    def test_error_creation(self) -> None:
        """Test error creation with key."""
        error = IdempotencyKeyConflictError("key-123")
        assert error.idempotency_key == "key-123"
        assert "key-123" in str(error)

    def test_error_message(self) -> None:
        """Test error message contains key and explanation."""
        error = IdempotencyKeyConflictError("abc-def")
        assert "abc-def" in str(error)
        assert "different request body" in str(error)

    def test_is_exception(self) -> None:
        """Test error is an Exception."""
        error = IdempotencyKeyConflictError("key")
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(IdempotencyKeyConflictError) as exc_info:
            raise IdempotencyKeyConflictError("test-key")
        assert exc_info.value.idempotency_key == "test-key"


class TestIdempotencyKeyMissingError:
    """Tests for IdempotencyKeyMissingError."""

    def test_error_creation(self) -> None:
        """Test error creation with endpoint."""
        error = IdempotencyKeyMissingError("/api/v1/orders")
        assert error.endpoint == "/api/v1/orders"
        assert "/api/v1/orders" in str(error)

    def test_error_message(self) -> None:
        """Test error message contains endpoint."""
        error = IdempotencyKeyMissingError("/api/payments")
        assert "Idempotency-Key header is required" in str(error)
        assert "/api/payments" in str(error)

    def test_is_exception(self) -> None:
        """Test error is an Exception."""
        error = IdempotencyKeyMissingError("/endpoint")
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(IdempotencyKeyMissingError) as exc_info:
            raise IdempotencyKeyMissingError("/api/test")
        assert exc_info.value.endpoint == "/api/test"
