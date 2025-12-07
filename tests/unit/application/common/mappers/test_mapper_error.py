"""Tests for mapper error module."""

import pytest

from application.common.mappers.errors.mapper_error import MapperError


class TestMapperError:
    """Tests for MapperError exception."""

    def test_init_with_message_only(self) -> None:
        error = MapperError("Test error")
        assert str(error) == "Test error"
        assert error.source_type is None
        assert error.target_type is None
        assert error.field is None
        assert error.context == {}

    def test_init_with_source_type(self) -> None:
        error = MapperError("Test error", source_type="UserEntity")
        assert error.source_type == "UserEntity"

    def test_init_with_target_type(self) -> None:
        error = MapperError("Test error", target_type="UserDTO")
        assert error.target_type == "UserDTO"

    def test_init_with_field(self) -> None:
        error = MapperError("Test error", field="email")
        assert error.field == "email"

    def test_init_with_context(self) -> None:
        context = {"key": "value", "count": 42}
        error = MapperError("Test error", context=context)
        assert error.context == context

    def test_init_with_all_params(self) -> None:
        error = MapperError(
            "Mapping failed",
            source_type="UserEntity",
            target_type="UserDTO",
            field="email",
            context={"reason": "invalid format"},
        )
        assert str(error) == "Mapping failed"
        assert error.source_type == "UserEntity"
        assert error.target_type == "UserDTO"
        assert error.field == "email"
        assert error.context == {"reason": "invalid format"}

    def test_is_exception(self) -> None:
        error = MapperError("Test error")
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        with pytest.raises(MapperError) as exc_info:
            raise MapperError("Test error", field="name")
        assert exc_info.value.field == "name"

    def test_context_defaults_to_empty_dict(self) -> None:
        error = MapperError("Test error", context=None)
        assert error.context == {}
