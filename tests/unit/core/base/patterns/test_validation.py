"""Tests for core/base/patterns/validation.py - Validation patterns."""

import pytest

from src.core.base.patterns.validation import (
    AlternativeValidator,
    ChainedValidator,
    FieldError,
    NotEmptyValidator,
    PredicateValidator,
    RangeValidator,
    ValidationError,
    validate_all,
)


class TestFieldError:
    """Tests for FieldError class."""

    def test_field_error_creation(self):
        error = FieldError(field="name", message="Name is required")
        assert error.field == "name"
        assert error.message == "Name is required"

    def test_field_error_default_code(self):
        error = FieldError(field="name", message="Error")
        assert error.code == "validation_error"

    def test_field_error_custom_code(self):
        error = FieldError(field="name", message="Error", code="custom_code")
        assert error.code == "custom_code"

    def test_field_error_with_value(self):
        error = FieldError(field="age", message="Invalid", value=150)
        assert error.value == 150

    def test_field_error_is_frozen(self):
        error = FieldError(field="name", message="Error")
        with pytest.raises(AttributeError):
            error.field = "other"


class TestValidationError:
    """Tests for ValidationError class."""

    def test_validation_error_creation(self):
        error = ValidationError(message="Validation failed")
        assert error.message == "Validation failed"

    def test_validation_error_empty_errors(self):
        error = ValidationError(message="Error")
        assert error.errors == []

    def test_validation_error_with_errors(self):
        field_errors = [FieldError(field="name", message="Required")]
        error = ValidationError(message="Error", errors=field_errors)
        assert len(error.errors) == 1

    def test_validation_error_with_context(self):
        error = ValidationError(message="Error", context="test_value")
        assert error.context == "test_value"

    def test_has_errors_true(self):
        error = ValidationError(
            message="Error",
            errors=[FieldError(field="name", message="Required")],
        )
        assert error.has_errors is True

    def test_has_errors_false(self):
        error = ValidationError(message="Error")
        assert error.has_errors is False

    def test_add_error_returns_new_instance(self):
        error = ValidationError(message="Error")
        new_error = error.add_error("name", "Required")
        assert error is not new_error
        assert len(error.errors) == 0
        assert len(new_error.errors) == 1

    def test_to_dict(self):
        error = ValidationError(
            message="Validation failed",
            errors=[FieldError(field="name", message="Required", code="required")],
        )
        d = error.to_dict()
        assert d["message"] == "Validation failed"
        assert len(d["errors"]) == 1
        assert d["errors"][0]["field"] == "name"


class TestPredicateValidator:
    """Tests for PredicateValidator class."""

    def test_valid_predicate(self):
        validator = PredicateValidator(lambda x: x > 0, "Must be positive")
        result = validator.validate(5)
        assert result.is_ok()
        assert result.unwrap() == 5

    def test_invalid_predicate(self):
        validator = PredicateValidator(lambda x: x > 0, "Must be positive")
        result = validator.validate(-1)
        assert result.is_err()

    def test_error_message(self):
        validator = PredicateValidator(lambda x: x > 0, "Must be positive")
        result = validator.validate(-1)
        assert result.error.message == "Must be positive"

    def test_custom_error_code(self):
        validator = PredicateValidator(lambda x: x > 0, "Must be positive", "positive_required")
        result = validator.validate(-1)
        assert result.error.errors[0].code == "positive_required"


class TestNotEmptyValidator:
    """Tests for NotEmptyValidator class."""

    def test_valid_string(self):
        validator = NotEmptyValidator()
        result = validator.validate("hello")
        assert result.is_ok()
        assert result.unwrap() == "hello"

    def test_empty_string(self):
        validator = NotEmptyValidator()
        result = validator.validate("")
        assert result.is_err()

    def test_whitespace_only(self):
        validator = NotEmptyValidator()
        result = validator.validate("   ")
        assert result.is_err()

    def test_string_with_whitespace(self):
        validator = NotEmptyValidator()
        result = validator.validate("  hello  ")
        assert result.is_ok()


class TestRangeValidator:
    """Tests for RangeValidator class."""

    def test_valid_in_range(self):
        validator = RangeValidator(min_value=0, max_value=100)
        result = validator.validate(50)
        assert result.is_ok()
        assert result.unwrap() == 50

    def test_below_min(self):
        validator = RangeValidator(min_value=0)
        result = validator.validate(-5)
        assert result.is_err()
        assert "min" in result.error.errors[0].code

    def test_above_max(self):
        validator = RangeValidator(max_value=100)
        result = validator.validate(150)
        assert result.is_err()
        assert "max" in result.error.errors[0].code

    def test_at_min_boundary(self):
        validator = RangeValidator(min_value=0)
        result = validator.validate(0)
        assert result.is_ok()

    def test_at_max_boundary(self):
        validator = RangeValidator(max_value=100)
        result = validator.validate(100)
        assert result.is_ok()

    def test_float_values(self):
        validator = RangeValidator(min_value=0.0, max_value=1.0)
        result = validator.validate(0.5)
        assert result.is_ok()


class TestChainedValidator:
    """Tests for ChainedValidator class."""

    def test_all_pass(self):
        validators = [
            PredicateValidator(lambda x: x > 0, "Must be positive"),
            PredicateValidator(lambda x: x < 100, "Must be less than 100"),
        ]
        chained = ChainedValidator(validators)
        result = chained.validate(50)
        assert result.is_ok()

    def test_first_fails(self):
        validators = [
            PredicateValidator(lambda x: x > 0, "Must be positive"),
            PredicateValidator(lambda x: x < 100, "Must be less than 100"),
        ]
        chained = ChainedValidator(validators)
        result = chained.validate(-5)
        assert result.is_err()
        assert "positive" in result.error.message

    def test_second_fails(self):
        validators = [
            PredicateValidator(lambda x: x > 0, "Must be positive"),
            PredicateValidator(lambda x: x < 100, "Must be less than 100"),
        ]
        chained = ChainedValidator(validators)
        result = chained.validate(150)
        assert result.is_err()
        assert "100" in result.error.message

    def test_empty_validators(self):
        chained = ChainedValidator([])
        result = chained.validate(50)
        assert result.is_ok()


class TestAlternativeValidator:
    """Tests for AlternativeValidator class."""

    def test_first_passes(self):
        validators = [
            PredicateValidator(lambda x: x > 0, "Must be positive"),
            PredicateValidator(lambda x: x < 0, "Must be negative"),
        ]
        alt = AlternativeValidator(validators)
        result = alt.validate(5)
        assert result.is_ok()

    def test_second_passes(self):
        validators = [
            PredicateValidator(lambda x: x > 100, "Must be > 100"),
            PredicateValidator(lambda x: x < 0, "Must be negative"),
        ]
        alt = AlternativeValidator(validators)
        result = alt.validate(-5)
        assert result.is_ok()

    def test_none_pass(self):
        validators = [
            PredicateValidator(lambda x: x > 100, "Must be > 100"),
            PredicateValidator(lambda x: x < 0, "Must be negative"),
        ]
        alt = AlternativeValidator(validators)
        result = alt.validate(50)
        assert result.is_err()


class TestValidateAll:
    """Tests for validate_all function."""

    def test_all_pass(self):
        validators = [
            PredicateValidator(lambda x: x > 0, "Must be positive"),
            PredicateValidator(lambda x: x < 100, "Must be < 100"),
        ]
        result = validate_all(50, validators)
        assert result.is_ok()

    def test_collects_all_errors(self):
        validators = [
            RangeValidator(min_value=10),
            RangeValidator(max_value=5),
        ]
        result = validate_all(7, validators)
        assert result.is_err()
        # Should have errors from both validators
        assert len(result.error.errors) == 2

    def test_empty_validators(self):
        result = validate_all(50, [])
        assert result.is_ok()


class TestValidatorChaining:
    """Tests for validator chaining methods."""

    def test_and_then(self):
        v1 = PredicateValidator(lambda x: x > 0, "Must be positive")
        v2 = PredicateValidator(lambda x: x < 100, "Must be < 100")
        chained = v1.and_then(v2)
        assert isinstance(chained, ChainedValidator)
        result = chained.validate(50)
        assert result.is_ok()

    def test_or_else(self):
        v1 = PredicateValidator(lambda x: x > 100, "Must be > 100")
        v2 = PredicateValidator(lambda x: x < 0, "Must be negative")
        alt = v1.or_else(v2)
        assert isinstance(alt, AlternativeValidator)
        result = alt.validate(-5)
        assert result.is_ok()
