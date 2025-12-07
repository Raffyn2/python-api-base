"""Tests for not found error class.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

import pytest

from application.common.errors.base.application_error import ApplicationError
from application.common.errors.not_found.not_found_error import NotFoundError


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_create_with_entity_type_and_id(self) -> None:
        """Test creating error with entity type and id."""
        error = NotFoundError(entity_type="User", entity_id="123")
        assert error.entity_type == "User"
        assert error.entity_id == "123"

    def test_message_format(self) -> None:
        """Test message format."""
        error = NotFoundError(entity_type="Order", entity_id="order-456")
        assert error.message == "Order with id 'order-456' not found"

    def test_error_code_is_not_found(self) -> None:
        """Test that error code is NOT_FOUND."""
        error = NotFoundError(entity_type="Test", entity_id="1")
        assert error.code == "NOT_FOUND"

    def test_details_contain_entity_info(self) -> None:
        """Test that details contain entity information."""
        error = NotFoundError(entity_type="Product", entity_id="prod-789")
        assert error.details["entity_type"] == "Product"
        assert error.details["entity_id"] == "prod-789"

    def test_inherits_from_application_error(self) -> None:
        """Test that NotFoundError inherits from ApplicationError."""
        error = NotFoundError(entity_type="Test", entity_id="1")
        assert isinstance(error, ApplicationError)

    def test_can_be_raised(self) -> None:
        """Test that error can be raised and caught."""
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError(entity_type="User", entity_id="user-123")
        assert exc_info.value.entity_type == "User"
        assert exc_info.value.entity_id == "user-123"

    def test_with_integer_id(self) -> None:
        """Test with integer entity id."""
        error = NotFoundError(entity_type="Item", entity_id=42)
        assert error.entity_id == 42
        assert error.details["entity_id"] == "42"

    def test_with_uuid_id(self) -> None:
        """Test with UUID entity id."""
        from uuid import UUID

        uuid_id = UUID("12345678-1234-5678-1234-567812345678")
        error = NotFoundError(entity_type="Document", entity_id=uuid_id)
        assert error.entity_id == uuid_id

    def test_str_representation(self) -> None:
        """Test string representation."""
        error = NotFoundError(entity_type="Category", entity_id="cat-1")
        assert str(error) == "Category with id 'cat-1' not found"

    def test_with_different_entity_types(self) -> None:
        """Test with different entity types."""
        entities = [
            ("User", "user-1"),
            ("Order", "order-2"),
            ("Product", "prod-3"),
            ("Invoice", "inv-4"),
        ]
        for entity_type, entity_id in entities:
            error = NotFoundError(entity_type=entity_type, entity_id=entity_id)
            assert error.entity_type == entity_type
            assert error.entity_id == entity_id
