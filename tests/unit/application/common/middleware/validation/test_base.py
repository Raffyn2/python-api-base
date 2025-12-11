"""Tests for application/common/middleware/validation/base.py - Base validators."""

from dataclasses import dataclass
from typing import Any

import pytest

from src.application.common.middleware.validation.base import (
    CompositeValidator,
    Validator,
)


@dataclass
class SampleCommand:
    """Sample command for testing validators."""

    name: str | None = None
    value: int | None = None


class AlwaysValidValidator(Validator):
    """Validator that always passes."""

    def validate(self, command: Any) -> list[dict[str, Any]]:
        return []


class AlwaysInvalidValidator(Validator):
    """Validator that always fails."""

    def __init__(self, error_message: str = "Always invalid"):
        self._error_message = error_message

    def validate(self, command: Any) -> list[dict[str, Any]]:
        return [{"field": "test", "message": self._error_message, "code": "invalid"}]


class NameRequiredValidator(Validator):
    """Validator that requires name field."""

    def validate(self, command: Any) -> list[dict[str, Any]]:
        if getattr(command, "name", None) is None:
            return [{"field": "name", "message": "name is required", "code": "required"}]
        return []


class ValuePositiveValidator(Validator):
    """Validator that requires positive value."""

    def validate(self, command: Any) -> list[dict[str, Any]]:
        value = getattr(command, "value", None)
        if value is not None and value <= 0:
            return [{"field": "value", "message": "value must be positive", "code": "positive"}]
        return []


class TestValidatorAbstract:
    """Tests for Validator abstract class."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Validator()

    def test_subclass_must_implement_validate(self):
        class IncompleteValidator(Validator):
            pass

        with pytest.raises(TypeError):
            IncompleteValidator()


class TestCompositeValidator:
    """Tests for CompositeValidator class."""

    def test_empty_validators_returns_empty(self):
        validator = CompositeValidator([])
        command = SampleCommand(name="test", value=10)
        errors = validator.validate(command)
        assert errors == []

    def test_single_valid_validator(self):
        validator = CompositeValidator([AlwaysValidValidator()])
        command = SampleCommand(name="test", value=10)
        errors = validator.validate(command)
        assert errors == []

    def test_single_invalid_validator(self):
        validator = CompositeValidator([AlwaysInvalidValidator()])
        command = SampleCommand(name="test", value=10)
        errors = validator.validate(command)
        assert len(errors) == 1

    def test_multiple_valid_validators(self):
        validator = CompositeValidator(
            [
                AlwaysValidValidator(),
                AlwaysValidValidator(),
                AlwaysValidValidator(),
            ]
        )
        command = SampleCommand(name="test", value=10)
        errors = validator.validate(command)
        assert errors == []

    def test_multiple_invalid_validators(self):
        validator = CompositeValidator(
            [
                AlwaysInvalidValidator("Error 1"),
                AlwaysInvalidValidator("Error 2"),
            ]
        )
        command = SampleCommand(name="test", value=10)
        errors = validator.validate(command)
        assert len(errors) == 2

    def test_mixed_validators(self):
        validator = CompositeValidator(
            [
                AlwaysValidValidator(),
                AlwaysInvalidValidator(),
                AlwaysValidValidator(),
            ]
        )
        command = SampleCommand(name="test", value=10)
        errors = validator.validate(command)
        assert len(errors) == 1

    def test_collects_all_errors(self):
        validator = CompositeValidator(
            [
                NameRequiredValidator(),
                ValuePositiveValidator(),
            ]
        )
        command = SampleCommand(name=None, value=-5)
        errors = validator.validate(command)
        assert len(errors) == 2
        fields = [e["field"] for e in errors]
        assert "name" in fields
        assert "value" in fields

    def test_passes_when_all_valid(self):
        validator = CompositeValidator(
            [
                NameRequiredValidator(),
                ValuePositiveValidator(),
            ]
        )
        command = SampleCommand(name="test", value=10)
        errors = validator.validate(command)
        assert errors == []

    def test_partial_validation_failure(self):
        validator = CompositeValidator(
            [
                NameRequiredValidator(),
                ValuePositiveValidator(),
            ]
        )
        command = SampleCommand(name="test", value=-5)
        errors = validator.validate(command)
        assert len(errors) == 1
        assert errors[0]["field"] == "value"


class TestCompositeValidatorNesting:
    """Tests for nested CompositeValidators."""

    def test_nested_composite_validators(self):
        inner = CompositeValidator(
            [
                NameRequiredValidator(),
            ]
        )
        outer = CompositeValidator(
            [
                inner,
                ValuePositiveValidator(),
            ]
        )
        command = SampleCommand(name=None, value=-5)
        errors = outer.validate(command)
        assert len(errors) == 2

    def test_deeply_nested_validators(self):
        level1 = CompositeValidator([AlwaysInvalidValidator("Level 1")])
        level2 = CompositeValidator([level1, AlwaysInvalidValidator("Level 2")])
        level3 = CompositeValidator([level2, AlwaysInvalidValidator("Level 3")])
        command = SampleCommand()
        errors = level3.validate(command)
        assert len(errors) == 3
