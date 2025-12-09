"""Unit tests for mapper error handling.

**Feature: test-coverage-90-percent**
**Validates: Requirements 1.1**
"""

import pytest

from application.common.mappers.errors.mapper_error import MapperError


class TestMapperError:
    """Tests for MapperError exception."""

    def test_create_with_message_only(self) -> None:
        """MapperError should accept message only."""
        error = MapperError("Mapping failed")
        
        assert str(error) == "Mapping failed"
        assert error.source_type is None
        assert error.target_type is None
        assert error.field is None
        assert error.context == {}

    def test_create_with_source_and_target_types(self) -> None:
        """MapperError should store source and target types."""
        error = MapperError(
            "Type mismatch",
            source_type="UserEntity",
            target_type="UserDTO"
        )
        
        assert error.source_type == "UserEntity"
        assert error.target_type == "UserDTO"

    def test_create_with_field(self) -> None:
        """MapperError should store field name."""
        error = MapperError(
            "Invalid field value",
            field="email"
        )
        
        assert error.field == "email"

    def test_create_with_context(self) -> None:
        """MapperError should store context dictionary."""
        context = {"value": "invalid", "expected": "string"}
        error = MapperError(
            "Validation failed",
            context=context
        )
        
        assert error.context == context

    def test_create_with_all_parameters(self) -> None:
        """MapperError should accept all parameters."""
        context = {"original_value": 123}
        error = MapperError(
            "Complete mapping error",
            source_type="Entity",
            target_type="DTO",
            field="id",
            context=context
        )
        
        assert str(error) == "Complete mapping error"
        assert error.source_type == "Entity"
        assert error.target_type == "DTO"
        assert error.field == "id"
        assert error.context == context

    def test_is_exception_subclass(self) -> None:
        """MapperError should be an Exception subclass."""
        error = MapperError("Test")
        
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """MapperError should be raisable and catchable."""
        with pytest.raises(MapperError) as exc_info:
            raise MapperError(
                "Mapping failed",
                source_type="Source",
                target_type="Target"
            )
        
        assert exc_info.value.source_type == "Source"
        assert exc_info.value.target_type == "Target"

    def test_context_defaults_to_empty_dict(self) -> None:
        """MapperError context should default to empty dict, not None."""
        error = MapperError("Test", context=None)
        
        assert error.context == {}
        assert isinstance(error.context, dict)
