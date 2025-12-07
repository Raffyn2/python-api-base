"""Tests for conflict error class.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

import pytest

from application.common.errors.base.application_error import ApplicationError
from application.common.errors.conflict.conflict_error import ConflictError


class TestConflictError:
    """Tests for ConflictError."""

    def test_create_with_message_only(self) -> None:
        """Test creating error with message only."""
        error = ConflictError("Resource already exists")
        assert error.message == "Resource already exists"
        assert error.details == {}

    def test_create_with_resource(self) -> None:
        """Test creating error with resource type."""
        error = ConflictError("Duplicate email", resource="User")
        assert error.details["resource"] == "User"

    def test_error_code_is_conflict(self) -> None:
        """Test that error code is CONFLICT."""
        error = ConflictError("Test")
        assert error.code == "CONFLICT"

    def test_inherits_from_application_error(self) -> None:
        """Test that ConflictError inherits from ApplicationError."""
        error = ConflictError("Test")
        assert isinstance(error, ApplicationError)

    def test_str_representation(self) -> None:
        """Test string representation."""
        error = ConflictError("User with email already exists")
        assert str(error) == "User with email already exists"

    def test_can_be_raised(self) -> None:
        """Test that error can be raised and caught."""
        with pytest.raises(ConflictError) as exc_info:
            raise ConflictError("Duplicate key", resource="Item")
        assert exc_info.value.details["resource"] == "Item"

    def test_details_empty_when_no_resource(self) -> None:
        """Test that details are empty when no resource provided."""
        error = ConflictError("Conflict occurred", resource=None)
        assert error.details == {}

    def test_with_different_resources(self) -> None:
        """Test with different resource types."""
        resources = ["User", "Order", "Product", "Category"]
        for resource in resources:
            error = ConflictError(f"Duplicate {resource}", resource=resource)
            assert error.details["resource"] == resource
