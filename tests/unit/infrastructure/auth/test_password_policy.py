"""Unit tests for infrastructure/auth/policies/password_policy.py.

Tests password validation, strength scoring, and hashing.

**Feature: test-coverage-90-percent**
**Validates: Requirements 4.1**
"""

import pytest

from infrastructure.auth.policies.password_policy import (
    COMMON_PASSWORD_PENALTY,
    LENGTH_BONUS_MULTIPLIER,
    MAX_LENGTH_BONUS,
    MAX_SCORE,
    SCORE_PER_REQUIREMENT,
    PasswordPolicy,
    PasswordValidationResult,
    PasswordValidator,
    get_password_validator,
)


class TestPasswordPolicy:
    """Tests for PasswordPolicy dataclass."""

    def test_default_policy(self) -> None:
        """Default policy should have sensible defaults."""
        policy = PasswordPolicy()

        assert policy.min_length == 12
        assert policy.max_length == 128
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digit is True
        assert policy.require_special is True
        assert policy.check_common_passwords is True

    def test_custom_policy(self) -> None:
        """Custom policy should accept custom values."""
        policy = PasswordPolicy(min_length=8, max_length=64, require_uppercase=False, require_special=False)

        assert policy.min_length == 8
        assert policy.max_length == 64
        assert policy.require_uppercase is False
        assert policy.require_special is False

    def test_policy_is_frozen(self) -> None:
        """Policy should be immutable."""
        policy = PasswordPolicy()

        with pytest.raises(AttributeError):
            policy.min_length = 20  # type: ignore


class TestPasswordValidationResult:
    """Tests for PasswordValidationResult dataclass."""

    def test_default_result(self) -> None:
        """Default result should be valid with no errors."""
        result = PasswordValidationResult(valid=True)

        assert result.valid is True
        assert result.errors == []
        assert result.strength_score == 0

    def test_add_error(self) -> None:
        """add_error should add error and set valid to False."""
        result = PasswordValidationResult(valid=True)

        result.add_error("Test error")

        assert result.valid is False
        assert "Test error" in result.errors

    def test_add_multiple_errors(self) -> None:
        """add_error should accumulate errors."""
        result = PasswordValidationResult(valid=True)

        result.add_error("Error 1")
        result.add_error("Error 2")

        assert len(result.errors) == 2


class TestPasswordValidator:
    """Tests for PasswordValidator class."""

    def test_init_with_default_policy(self) -> None:
        """Validator should use default policy if none provided."""
        validator = PasswordValidator()

        assert validator.policy.min_length == 12

    def test_init_with_custom_policy(self) -> None:
        """Validator should use provided policy."""
        policy = PasswordPolicy(min_length=8)
        validator = PasswordValidator(policy)

        assert validator.policy.min_length == 8

    def test_validate_strong_password(self) -> None:
        """Strong password should pass validation."""
        validator = PasswordValidator()

        result = validator.validate("StrongP@ssw0rd123!")

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.strength_score > 0

    def test_validate_too_short(self) -> None:
        """Password shorter than min_length should fail."""
        validator = PasswordValidator()

        result = validator.validate("Short1!")

        assert result.valid is False
        assert any("at least" in e and "characters" in e for e in result.errors)

    def test_validate_too_long(self) -> None:
        """Password longer than max_length should fail."""
        policy = PasswordPolicy(max_length=20)
        validator = PasswordValidator(policy)

        result = validator.validate("A" * 21 + "a1!")

        assert result.valid is False
        assert any("at most" in e for e in result.errors)

    def test_validate_missing_uppercase(self) -> None:
        """Password without uppercase should fail if required."""
        validator = PasswordValidator()

        result = validator.validate("lowercase123!@#")

        assert result.valid is False
        assert any("uppercase" in e for e in result.errors)

    def test_validate_missing_lowercase(self) -> None:
        """Password without lowercase should fail if required."""
        validator = PasswordValidator()

        result = validator.validate("UPPERCASE123!@#")

        assert result.valid is False
        assert any("lowercase" in e for e in result.errors)

    def test_validate_missing_digit(self) -> None:
        """Password without digit should fail if required."""
        validator = PasswordValidator()

        result = validator.validate("NoDigitsHere!@#")

        assert result.valid is False
        assert any("digit" in e for e in result.errors)

    def test_validate_missing_special(self) -> None:
        """Password without special char should fail if required."""
        validator = PasswordValidator()

        result = validator.validate("NoSpecialChars123")

        assert result.valid is False
        assert any("special character" in e for e in result.errors)

    def test_validate_common_password(self) -> None:
        """Common password should fail if check enabled."""
        validator = PasswordValidator()

        result = validator.validate("password")

        assert result.valid is False
        assert any("common" in e.lower() for e in result.errors)

    def test_validate_common_password_disabled(self) -> None:
        """Common password should pass if check disabled."""
        policy = PasswordPolicy(
            min_length=8,
            require_uppercase=False,
            require_lowercase=True,
            require_digit=False,
            require_special=False,
            check_common_passwords=False,
        )
        validator = PasswordValidator(policy)

        result = validator.validate("password")

        # Should only fail on other requirements, not common password
        assert not any("common" in e.lower() for e in result.errors)

    def test_is_valid_returns_bool(self) -> None:
        """is_valid should return boolean."""
        validator = PasswordValidator()

        assert validator.is_valid("StrongP@ssw0rd123!") is True
        assert validator.is_valid("weak") is False

    def test_get_requirements(self) -> None:
        """get_requirements should return list of requirements."""
        validator = PasswordValidator()

        requirements = validator.get_requirements()

        assert len(requirements) > 0
        assert any("12 characters" in r for r in requirements)
        assert any("uppercase" in r.lower() for r in requirements)
        assert any("lowercase" in r.lower() for r in requirements)
        assert any("digit" in r.lower() for r in requirements)
        assert any("special" in r.lower() for r in requirements)

    def test_get_requirements_custom_policy(self) -> None:
        """get_requirements should reflect custom policy."""
        policy = PasswordPolicy(min_length=8, require_uppercase=False, require_special=False)
        validator = PasswordValidator(policy)

        requirements = validator.get_requirements()

        assert any("8 characters" in r for r in requirements)
        assert not any("uppercase" in r.lower() for r in requirements)
        assert not any("special" in r.lower() for r in requirements)

    def test_strength_score_calculation(self) -> None:
        """Strength score should increase with requirements met."""
        validator = PasswordValidator()

        # Weak password
        weak_result = validator.validate("weak")

        # Strong password
        strong_result = validator.validate("VeryStr0ng!P@ssword")

        assert strong_result.strength_score > weak_result.strength_score

    def test_length_bonus(self) -> None:
        """Extra length should add bonus to score."""
        policy = PasswordPolicy(min_length=8)
        validator = PasswordValidator(policy)

        # Minimum length
        min_result = validator.validate("Str0ng!A")

        # Extra length
        long_result = validator.validate("Str0ng!A" + "x" * 10)

        assert long_result.strength_score >= min_result.strength_score

    def test_hash_password_valid(self) -> None:
        """hash_password should hash valid password."""
        validator = PasswordValidator()
        password = "StrongP@ssw0rd123!"

        hashed = validator.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_invalid_raises(self) -> None:
        """hash_password should raise for invalid password."""
        validator = PasswordValidator()

        with pytest.raises(ValueError, match="does not meet policy"):
            validator.hash_password("weak")

    def test_verify_password(self) -> None:
        """verify_password should verify correct password."""
        validator = PasswordValidator()
        password = "StrongP@ssw0rd123!"

        hashed = validator.hash_password(password)

        assert validator.verify_password(password, hashed) is True
        assert validator.verify_password("wrong", hashed) is False


class TestGetPasswordValidator:
    """Tests for get_password_validator function."""

    def test_returns_validator(self) -> None:
        """get_password_validator should return PasswordValidator."""
        validator = get_password_validator()

        assert isinstance(validator, PasswordValidator)

    def test_returns_same_instance(self) -> None:
        """get_password_validator should return singleton."""
        validator1 = get_password_validator()
        validator2 = get_password_validator()

        assert validator1 is validator2


class TestConstants:
    """Tests for module constants."""

    def test_score_per_requirement(self) -> None:
        """SCORE_PER_REQUIREMENT should be positive."""
        assert SCORE_PER_REQUIREMENT > 0

    def test_max_score(self) -> None:
        """MAX_SCORE should be 100."""
        assert MAX_SCORE == 100

    def test_length_bonus_multiplier(self) -> None:
        """LENGTH_BONUS_MULTIPLIER should be positive."""
        assert LENGTH_BONUS_MULTIPLIER > 0

    def test_max_length_bonus(self) -> None:
        """MAX_LENGTH_BONUS should be positive."""
        assert MAX_LENGTH_BONUS > 0

    def test_common_password_penalty(self) -> None:
        """COMMON_PASSWORD_PENALTY should be positive."""
        assert COMMON_PASSWORD_PENALTY > 0
