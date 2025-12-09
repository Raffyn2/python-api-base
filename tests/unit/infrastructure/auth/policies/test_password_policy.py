"""Unit tests for password policy validation.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 4.2, 10.1, 10.2, 10.3, 10.4, 10.5**
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from infrastructure.auth.policies.password_policy import (
    PasswordPolicy,
    PasswordValidationResult,
    PasswordValidator,
    get_password_validator,
)


class TestPasswordPolicy:
    """Tests for PasswordPolicy dataclass."""

    def test_default_policy_values(self) -> None:
        """Test default policy values."""
        policy = PasswordPolicy()
        
        assert policy.min_length == 12
        assert policy.max_length == 128
        assert policy.require_uppercase is True
        assert policy.require_lowercase is True
        assert policy.require_digit is True
        assert policy.require_special is True
        assert policy.check_common_passwords is True

    def test_custom_policy_values(self) -> None:
        """Test custom policy values."""
        policy = PasswordPolicy(
            min_length=8,
            max_length=64,
            require_uppercase=False,
            require_special=False,
        )
        
        assert policy.min_length == 8
        assert policy.max_length == 64
        assert policy.require_uppercase is False
        assert policy.require_special is False


class TestPasswordValidationResult:
    """Tests for PasswordValidationResult."""

    def test_initial_valid_state(self) -> None:
        """Test initial valid state."""
        result = PasswordValidationResult(valid=True)
        
        assert result.valid is True
        assert result.errors == []
        assert result.strength_score == 0

    def test_add_error_sets_invalid(self) -> None:
        """Test adding error sets valid to False."""
        result = PasswordValidationResult(valid=True)
        result.add_error("Test error")
        
        assert result.valid is False
        assert "Test error" in result.errors


class TestPasswordValidator:
    """Tests for PasswordValidator."""

    @pytest.fixture
    def validator(self) -> PasswordValidator:
        """Create default validator."""
        return PasswordValidator()

    @pytest.fixture
    def lenient_validator(self) -> PasswordValidator:
        """Create lenient validator."""
        return PasswordValidator(
            PasswordPolicy(
                min_length=8,
                require_uppercase=False,
                require_lowercase=False,
                require_digit=False,
                require_special=False,
                check_common_passwords=False,
            )
        )

    def test_valid_password(self, validator: PasswordValidator) -> None:
        """Test valid password passes validation."""
        result = validator.validate("SecureP@ssw0rd123!")
        
        assert result.valid is True
        assert result.errors == []
        assert result.strength_score > 0

    def test_password_too_short(self, validator: PasswordValidator) -> None:
        """Test short password fails."""
        result = validator.validate("Short1!")
        
        assert result.valid is False
        assert any("at least" in e for e in result.errors)

    def test_password_too_long(self, validator: PasswordValidator) -> None:
        """Test long password fails."""
        long_password = "A" * 200 + "a1!"
        result = validator.validate(long_password)
        
        assert result.valid is False
        assert any("at most" in e for e in result.errors)

    def test_missing_uppercase(self, validator: PasswordValidator) -> None:
        """Test missing uppercase fails."""
        result = validator.validate("lowercase123!@#")
        
        assert result.valid is False
        assert any("uppercase" in e for e in result.errors)

    def test_missing_lowercase(self, validator: PasswordValidator) -> None:
        """Test missing lowercase fails."""
        result = validator.validate("UPPERCASE123!@#")
        
        assert result.valid is False
        assert any("lowercase" in e for e in result.errors)

    def test_missing_digit(self, validator: PasswordValidator) -> None:
        """Test missing digit fails."""
        result = validator.validate("NoDigitsHere!@#")
        
        assert result.valid is False
        assert any("digit" in e for e in result.errors)

    def test_missing_special(self, validator: PasswordValidator) -> None:
        """Test missing special character fails."""
        result = validator.validate("NoSpecialChar123")
        
        assert result.valid is False
        assert any("special" in e for e in result.errors)

    def test_common_password_rejected(self, validator: PasswordValidator) -> None:
        """Test common password is rejected."""
        result = validator.validate("password")
        
        assert result.valid is False
        assert any("common" in e for e in result.errors)

    def test_is_valid_returns_bool(self, validator: PasswordValidator) -> None:
        """Test is_valid returns boolean."""
        assert validator.is_valid("SecureP@ssw0rd123!") is True
        assert validator.is_valid("weak") is False

    def test_get_requirements(self, validator: PasswordValidator) -> None:
        """Test get_requirements returns list."""
        requirements = validator.get_requirements()
        
        assert isinstance(requirements, list)
        assert len(requirements) > 0
        assert any("12 characters" in r for r in requirements)

    def test_policy_property(self, validator: PasswordValidator) -> None:
        """Test policy property returns policy."""
        policy = validator.policy
        
        assert isinstance(policy, PasswordPolicy)
        assert policy.min_length == 12

    def test_lenient_policy_accepts_simple(
        self, lenient_validator: PasswordValidator
    ) -> None:
        """Test lenient policy accepts simple passwords."""
        result = lenient_validator.validate("simplepassword")
        
        assert result.valid is True

    def test_hash_password_valid(self, validator: PasswordValidator) -> None:
        """Test hashing valid password."""
        password = "SecureP@ssw0rd123!"
        hashed = validator.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_invalid_raises(self, validator: PasswordValidator) -> None:
        """Test hashing invalid password raises."""
        with pytest.raises(ValueError, match="does not meet policy"):
            validator.hash_password("weak")

    def test_verify_password(self, validator: PasswordValidator) -> None:
        """Test password verification."""
        password = "SecureP@ssw0rd123!"
        hashed = validator.hash_password(password)
        
        assert validator.verify_password(password, hashed) is True
        assert validator.verify_password("wrong", hashed) is False


class TestGetPasswordValidator:
    """Tests for get_password_validator function."""

    def test_returns_validator(self) -> None:
        """Test returns PasswordValidator instance."""
        validator = get_password_validator()
        
        assert isinstance(validator, PasswordValidator)

    def test_returns_same_instance(self) -> None:
        """Test returns same instance (singleton)."""
        v1 = get_password_validator()
        v2 = get_password_validator()
        
        assert v1 is v2


class TestPasswordStrengthScore:
    """Tests for password strength scoring."""

    @pytest.fixture
    def validator(self) -> PasswordValidator:
        """Create default validator."""
        return PasswordValidator()

    def test_strong_password_high_score(self, validator: PasswordValidator) -> None:
        """Test strong password gets high score."""
        result = validator.validate("VerySecureP@ssw0rd123!")
        
        assert result.strength_score >= 80

    def test_longer_password_bonus(self, validator: PasswordValidator) -> None:
        """Test longer passwords get bonus score."""
        short_result = validator.validate("SecureP@ss1!")
        long_result = validator.validate("VeryLongSecureP@ssw0rd123!")
        
        assert long_result.strength_score >= short_result.strength_score


class TestPasswordValidatorProperties:
    """Property-based tests for password validation.

    **Feature: test-coverage-80-percent-v3, Property 10: Password Hash Verification**
    **Validates: Requirements 4.2**
    """

    @given(
        password=st.text(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%",
            min_size=12,
            max_size=50,
        ).filter(
            lambda p: any(c.isupper() for c in p)
            and any(c.islower() for c in p)
            and any(c.isdigit() for c in p)
            and any(c in "!@#$%" for c in p)
        )
    )
    @settings(max_examples=20, deadline=10000)
    def test_valid_password_always_passes(self, password: str) -> None:
        """Property: Valid passwords always pass validation."""
        validator = PasswordValidator(
            PasswordPolicy(check_common_passwords=False)
        )
        
        result = validator.validate(password)
        assert result.valid is True

    @given(
        password=st.text(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%",
            min_size=12,
            max_size=30,
        ).filter(
            lambda p: any(c.isupper() for c in p)
            and any(c.islower() for c in p)
            and any(c.isdigit() for c in p)
            and any(c in "!@#$%" for c in p)
        )
    )
    @settings(max_examples=10, deadline=15000)
    def test_hash_verify_round_trip(self, password: str) -> None:
        """Property: Hashed password can be verified."""
        validator = PasswordValidator(
            PasswordPolicy(check_common_passwords=False)
        )
        
        hashed = validator.hash_password(password)
        assert validator.verify_password(password, hashed) is True
