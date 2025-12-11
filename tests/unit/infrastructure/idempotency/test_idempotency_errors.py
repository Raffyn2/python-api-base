"""Unit tests for idempotency errors.

Tests IdempotencyKeyConflictError and IdempotencyKeyMissingError.
"""

import pytest

from infrastructure.idempotency.errors import (
    IdempotencyKeyConflictError,
    IdempotencyKeyMissingError,
)


class TestIdempotencyKeyConflictError:
    """Tests for IdempotencyKeyConflictError."""

    def test_creation(self) -> None:
        """Test error creation."""
        error = IdempotencyKeyConflictError("key-123")

        assert error.idempotency_key == "key-123"
        assert "key-123" in str(error)
        assert "different request body" in str(error)

    def test_is_exception(self) -> None:
        """Test error is an exception."""
        error = IdempotencyKeyConflictError("key-123")

        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(IdempotencyKeyConflictError) as exc_info:
            raise IdempotencyKeyConflictError("test-key")

        assert exc_info.value.idempotency_key == "test-key"


class TestIdempotencyKeyMissingError:
    """Tests for IdempotencyKeyMissingError."""

    def test_creation(self) -> None:
        """Test error creation."""
        error = IdempotencyKeyMissingError("/api/orders")

        assert error.endpoint == "/api/orders"
        assert "/api/orders" in str(error)
        assert "required" in str(error).lower()

    def test_is_exception(self) -> None:
        """Test error is an exception."""
        error = IdempotencyKeyMissingError("/api/payments")

        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Test error can be raised and caught."""
        with pytest.raises(IdempotencyKeyMissingError) as exc_info:
            raise IdempotencyKeyMissingError("/api/test")

        assert exc_info.value.endpoint == "/api/test"
