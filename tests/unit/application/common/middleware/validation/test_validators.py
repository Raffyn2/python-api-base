"""Tests for application/common/middleware/validation/validators.py - Validators."""

from dataclasses import dataclass

import pytest

from src.application.common.middleware.validation.validators import (
    RangeValidator,
    RequiredFieldValidator,
    StringLengthValidator,
)


@dataclass
class SampleCommand:
    """Sample command for testing validators."""

    name: str | None = None
    email: str | None = None
    age: int | None = None
    price: float | None = None


class TestRequiredFieldValidator:
    """Tests for RequiredFieldValidator class."""

    def test_valid_when_field_present(self):
        validator = RequiredFieldValidator(["name"])
        command = SampleCommand(name="test")
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_error_when_field_none(self):
        validator = RequiredFieldValidator(["name"])
        command = SampleCommand(name=None)
        errors = validator.validate(command)
        assert len(errors) == 1
        assert errors[0]["field"] == "name"
        assert errors[0]["code"] == "required"

    def test_error_when_field_empty_string(self):
        validator = RequiredFieldValidator(["name"])
        command = SampleCommand(name="")
        errors = validator.validate(command)
        assert len(errors) == 1

    def test_error_when_field_whitespace_only(self):
        validator = RequiredFieldValidator(["name"])
        command = SampleCommand(name="   ")
        errors = validator.validate(command)
        assert len(errors) == 1

    def test_multiple_required_fields(self):
        validator = RequiredFieldValidator(["name", "email"])
        command = SampleCommand(name=None, email=None)
        errors = validator.validate(command)
        assert len(errors) == 2

    def test_partial_fields_present(self):
        validator = RequiredFieldValidator(["name", "email"])
        command = SampleCommand(name="test", email=None)
        errors = validator.validate(command)
        assert len(errors) == 1
        assert errors[0]["field"] == "email"

    def test_error_message_contains_field_name(self):
        validator = RequiredFieldValidator(["name"])
        command = SampleCommand(name=None)
        errors = validator.validate(command)
        assert "name" in errors[0]["message"]


class TestStringLengthValidator:
    """Tests for StringLengthValidator class."""

    def test_valid_within_range(self):
        validator = StringLengthValidator("name", min_length=2, max_length=10)
        command = SampleCommand(name="test")
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_error_below_min_length(self):
        validator = StringLengthValidator("name", min_length=5)
        command = SampleCommand(name="abc")
        errors = validator.validate(command)
        assert len(errors) == 1
        assert errors[0]["code"] == "min_length"

    def test_error_above_max_length(self):
        validator = StringLengthValidator("name", max_length=5)
        command = SampleCommand(name="toolongname")
        errors = validator.validate(command)
        assert len(errors) == 1
        assert errors[0]["code"] == "max_length"

    def test_valid_at_min_length(self):
        validator = StringLengthValidator("name", min_length=4)
        command = SampleCommand(name="test")
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_valid_at_max_length(self):
        validator = StringLengthValidator("name", max_length=4)
        command = SampleCommand(name="test")
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_no_error_when_field_none(self):
        validator = StringLengthValidator("name", min_length=5)
        command = SampleCommand(name=None)
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_no_error_when_field_not_string(self):
        validator = StringLengthValidator("age", min_length=5)
        command = SampleCommand(age=25)
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_error_message_contains_min_length(self):
        validator = StringLengthValidator("name", min_length=10)
        command = SampleCommand(name="short")
        errors = validator.validate(command)
        assert "10" in errors[0]["message"]

    def test_error_message_contains_max_length(self):
        validator = StringLengthValidator("name", max_length=5)
        command = SampleCommand(name="toolong")
        errors = validator.validate(command)
        assert "5" in errors[0]["message"]


class TestRangeValidator:
    """Tests for RangeValidator class."""

    def test_valid_within_range(self):
        validator = RangeValidator("age", min_value=18, max_value=100)
        command = SampleCommand(age=25)
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_error_below_min_value(self):
        validator = RangeValidator("age", min_value=18)
        command = SampleCommand(age=15)
        errors = validator.validate(command)
        assert len(errors) == 1
        assert errors[0]["code"] == "min_value"

    def test_error_above_max_value(self):
        validator = RangeValidator("age", max_value=100)
        command = SampleCommand(age=150)
        errors = validator.validate(command)
        assert len(errors) == 1
        assert errors[0]["code"] == "max_value"

    def test_valid_at_min_value(self):
        validator = RangeValidator("age", min_value=18)
        command = SampleCommand(age=18)
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_valid_at_max_value(self):
        validator = RangeValidator("age", max_value=100)
        command = SampleCommand(age=100)
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_no_error_when_field_none(self):
        validator = RangeValidator("age", min_value=18)
        command = SampleCommand(age=None)
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_no_error_when_field_not_numeric(self):
        validator = RangeValidator("name", min_value=0)
        command = SampleCommand(name="test")
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_works_with_float(self):
        validator = RangeValidator("price", min_value=0.0, max_value=1000.0)
        command = SampleCommand(price=99.99)
        errors = validator.validate(command)
        assert len(errors) == 0

    def test_float_below_min(self):
        validator = RangeValidator("price", min_value=10.0)
        command = SampleCommand(price=5.5)
        errors = validator.validate(command)
        assert len(errors) == 1

    def test_float_above_max(self):
        validator = RangeValidator("price", max_value=100.0)
        command = SampleCommand(price=150.5)
        errors = validator.validate(command)
        assert len(errors) == 1

    def test_error_message_contains_min_value(self):
        validator = RangeValidator("age", min_value=18)
        command = SampleCommand(age=10)
        errors = validator.validate(command)
        assert "18" in errors[0]["message"]

    def test_error_message_contains_max_value(self):
        validator = RangeValidator("age", max_value=100)
        command = SampleCommand(age=150)
        errors = validator.validate(command)
        assert "100" in errors[0]["message"]


class TestValidatorCombinations:
    """Tests for combining multiple validators."""

    def test_multiple_validators_all_pass(self):
        validators = [
            RequiredFieldValidator(["name"]),
            StringLengthValidator("name", min_length=2, max_length=50),
        ]
        command = SampleCommand(name="test")
        all_errors = []
        for v in validators:
            all_errors.extend(v.validate(command))
        assert len(all_errors) == 0

    def test_multiple_validators_some_fail(self):
        validators = [
            RequiredFieldValidator(["name", "email"]),
            StringLengthValidator("name", min_length=10),
        ]
        command = SampleCommand(name="test", email=None)
        all_errors = []
        for v in validators:
            all_errors.extend(v.validate(command))
        assert len(all_errors) == 2  # email required + name too short
