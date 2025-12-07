"""Tests for password policy module."""

import pytest

from infrastructure.auth.policies.password_policy import (
    PasswordPolicy,
    PasswordValidationResult,
    PasswordValidator,
    get_password_validator,
)


class TestPasswordPolicy:
    """Tests for PasswordPolicy dataclass."""

    def test_default_values(self) -> None:
        policy = PasswordPolicy()
        assert policy.min_length == 12
        assert policy.max_length == 128
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digit is True
        assert policy.require_special is True
        assert policy.check_common_passwords is True

    def test_custom_min_length(self) -> None:
        policy = PasswordPolicy(min_length=8)
        assert policy.min_length == 8

    def test_custom_max_length(self) -> None:
        policy = PasswordPolicy(max_length=64)
        assert policy.max_length == 64

    def test_disable_uppercase_requirement(self) -> None:
        policy = PasswordPolicy(require_uppercase=False)
        assert policy.require_uppercase is False

    def test_disable_lowercase_requirement(self) -> None:
        policy = PasswordPolicy(require_lowercase=False)
        assert policy.require_lowercase is False

    def test_disable_digit_requirement(self) -> None:
        policy = PasswordPolicy(require_digit=False)
        assert policy.require_digit is False

    def test_disable_special_requirement(self) -> None:
        policy = PasswordPolicy(require_special=False)
        assert policy.require_special is False

    def test_disable_common_password_check(self) -> None:
        policy = PasswordPolicy(check_common_passwords=False)
        assert policy.check_common_passwords is False

    def test_custom_special_characters(self) -> None:
        policy = PasswordPolicy(special_characters="!@#$")
        assert policy.special_characters == "!@#$"

    def test_policy_is_frozen(self) -> None:
        policy = PasswordPolicy()
        with pytest.raises(AttributeError):
            policy.min_length = 20  # type: ignore


class TestPasswordValidationResult:
    """Tests for PasswordValidationResult dataclass."""

    def test_default_valid(self) -> None:
        result = PasswordValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.strength_score == 0

    def test_invalid_result(self) -> None:
        result = PasswordValidationResult(valid=False, errors=["Too short"])
        assert result.valid is False
        assert "Too short" in result.errors

    def test_add_error(self) -> None:
        result = PasswordValidationResult(valid=True)
        result.add_error("Missing uppercase")
        assert result.valid is False
        assert "Missing uppercase" in result.errors

    def test_add_multiple_errors(self) -> None:
        result = PasswordValidationResult(valid=True)
        result.add_error("Error 1")
        result.add_error("Error 2")
        assert len(result.errors) == 2

    def test_strength_score(self) -> None:
        result = PasswordValidationResult(valid=True, strength_score=80)
        assert result.strength_score == 80


class TestPasswordValidator:
    """Tests for PasswordValidator class."""

    def test_init_with_default_policy(self) -> None:
        validator = PasswordValidator()
        assert validator.policy.min_length == 12

    def test_init_with_custom_policy(self) -> None:
        policy = PasswordPolicy(min_length=8)
        validator = PasswordValidator(policy)
        assert validator.policy.min_length == 8

    def test_policy_property(self) -> None:
        validator = PasswordValidator()
        assert isinstance(validator.policy, PasswordPolicy)

    def test_validate_too_short(self) -> None:
        validator = PasswordValidator()
        result = validator.validate("Short1!")
        assert result.valid is False
        assert any("at least" in e for e in result.errors)

    def test_validate_too_long(self) -> None:
        policy = PasswordPolicy(max_length=20)
        validator = PasswordValidator(policy)
        result = validator.validate("A" * 21 + "a1!")
        assert result.valid is False
        assert any("at most" in e for e in result.errors)

    def test_validate_missing_uppercase(self) -> None:
        validator = PasswordValidator()
        result = validator.validate("lowercase123!@#")
        assert result.valid is False
        assert any("uppercase" in e for e in result.errors)

    def test_validate_missing_lowercase(self) -> None:
        validator = PasswordValidator()
        result = validator.validate("UPPERCASE123!@#")
        assert result.valid is False
        assert any("lowercase" in e for e in result.errors)

    def test_validate_missing_digit(self) -> None:
        validator = PasswordValidator()
        result = validator.validate("NoDigitsHere!@#")
        assert result.valid is False
        assert any("digit" in e for e in result.errors)

    def test_validate_missing_special(self) -> None:
        validator = PasswordValidator()
        result = validator.validate("NoSpecialChar123")
        assert result.valid is False
        assert any("special" in e for e in result.errors)

    def test_validate_common_password(self) -> None:
        validator = PasswordValidator()
        result = validator.validate("password")
        assert result.valid is False
        assert any("common" in e for e in result.errors)

    def test_validate_valid_password(self) -> None:
        validator = PasswordValidator()
        result = validator.validate("SecureP@ssw0rd123!")
        assert result.valid is True
        assert result.errors == []
        assert result.strength_score > 0

    def test_validate_with_relaxed_policy(self) -> None:
        policy = PasswordPolicy(
            min_length=4,
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
            require_special=False,
            check_common_passwords=False,
        )
        validator = PasswordValidator(policy)
        result = validator.validate("test")
        assert result.valid is True

    def test_is_valid_returns_bool(self) -> None:
        validator = PasswordValidator()
        assert validator.is_valid("SecureP@ssw0rd123!") is True
        assert validator.is_valid("weak") is False

    def test_get_requirements(self) -> None:
        validator = PasswordValidator()
        requirements = validator.get_requirements()
        assert isinstance(requirements, list)
        assert len(requirements) > 0
        assert any("12" in r for r in requirements)  # min length
        assert any("uppercase" in r.lower() for r in requirements)
        assert any("lowercase" in r.lower() for r in requirements)
        assert any("digit" in r.lower() for r in requirements)
        assert any("special" in r.lower() for r in requirements)

    def test_get_requirements_with_disabled_options(self) -> None:
        policy = PasswordPolicy(
            require_uppercase=False,
            require_special=False,
            check_common_passwords=False,
        )
        validator = PasswordValidator(policy)
        requirements = validator.get_requirements()
        assert not any("uppercase" in r.lower() for r in requirements)
        assert not any("special" in r.lower() for r in requirements)

    def test_strength_score_increases_with_length(self) -> None:
        validator = PasswordValidator()
        short_result = validator.validate("SecureP@ss1!")
        long_result = validator.validate("SecureP@ssword123!Extra")
        assert long_result.strength_score >= short_result.strength_score

    def test_common_password_reduces_score(self) -> None:
        policy = PasswordPolicy(min_length=4, check_common_passwords=True)
        validator = PasswordValidator(policy)
        # Common password should have penalty
        result = validator.validate("password")
        assert result.strength_score < 60


class TestHashAndVerify:
    """Tests for password hashing and verification."""

    def test_hash_password_valid(self) -> None:
        validator = PasswordValidator()
        hashed = validator.hash_password("SecureP@ssw0rd123!")
        assert hashed != "SecureP@ssw0rd123!"
        assert len(hashed) > 0

    def test_hash_password_invalid_raises(self) -> None:
        validator = PasswordValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.hash_password("weak")
        assert "does not meet policy" in str(exc_info.value)

    def test_verify_password_correct(self) -> None:
        validator = PasswordValidator()
        password = "SecureP@ssw0rd123!"
        hashed = validator.hash_password(password)
        assert validator.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        validator = PasswordValidator()
        password = "SecureP@ssw0rd123!"
        hashed = validator.hash_password(password)
        assert validator.verify_password("WrongPassword1!", hashed) is False


class TestGetPasswordValidator:
    """Tests for get_password_validator function."""

    def test_returns_validator(self) -> None:
        validator = get_password_validator()
        assert isinstance(validator, PasswordValidator)

    def test_returns_same_instance(self) -> None:
        v1 = get_password_validator()
        v2 = get_password_validator()
        assert v1 is v2

    def test_validator_has_default_policy(self) -> None:
        validator = get_password_validator()
        assert validator.policy.min_length == 12
