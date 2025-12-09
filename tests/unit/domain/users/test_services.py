"""Unit tests for domain/users/services/services.py.

Tests user domain services.

**Task 8.4: Create tests for user domain services**
**Requirements: 2.2**
"""

import pytest

from domain.users.services.services import (
    EmailValidator,
    PasswordHasher,
    UserDomainService,
)


class MockPasswordHasher:
    """Mock password hasher for testing."""

    def hash(self, password: str) -> str:
        return f"hashed_{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed_{password}"


class MockEmailValidator:
    """Mock email validator for testing."""

    def __init__(self, disposable_domains: list[str] | None = None) -> None:
        self.disposable_domains = disposable_domains or []

    def is_valid(self, email: str) -> bool:
        return "@" in email and "." in email.split("@")[1]

    def is_disposable(self, email: str) -> bool:
        domain = email.split("@")[1] if "@" in email else ""
        return domain in self.disposable_domains


class TestUserDomainServiceHashPassword:
    """Tests for UserDomainService.hash_password method."""

    def test_hash_password(self) -> None:
        """Test password hashing."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        result = service.hash_password("mypassword")

        assert result == "hashed_mypassword"


class TestUserDomainServiceVerifyPassword:
    """Tests for UserDomainService.verify_password method."""

    def test_verify_correct_password(self) -> None:
        """Test verifying correct password."""
        service = UserDomainService(password_hasher=MockPasswordHasher())
        hashed = service.hash_password("mypassword")

        result = service.verify_password("mypassword", hashed)

        assert result is True

    def test_verify_wrong_password(self) -> None:
        """Test verifying wrong password."""
        service = UserDomainService(password_hasher=MockPasswordHasher())
        hashed = service.hash_password("mypassword")

        result = service.verify_password("wrongpassword", hashed)

        assert result is False


class TestUserDomainServiceValidateEmail:
    """Tests for UserDomainService.validate_email method."""

    def test_valid_email_basic(self) -> None:
        """Test valid email with basic validation."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, error = service.validate_email("user@example.com")

        assert is_valid is True
        assert error is None

    def test_invalid_email_basic(self) -> None:
        """Test invalid email with basic validation."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, error = service.validate_email("invalid-email")

        assert is_valid is False
        assert error == "Invalid email format"

    def test_valid_email_with_validator(self) -> None:
        """Test valid email with custom validator."""
        validator = MockEmailValidator()
        service = UserDomainService(
            password_hasher=MockPasswordHasher(), email_validator=validator
        )

        is_valid, error = service.validate_email("user@example.com")

        assert is_valid is True
        assert error is None

    def test_disposable_email_rejected(self) -> None:
        """Test disposable email is rejected."""
        validator = MockEmailValidator(disposable_domains=["tempmail.com"])
        service = UserDomainService(
            password_hasher=MockPasswordHasher(), email_validator=validator
        )

        is_valid, error = service.validate_email("user@tempmail.com")

        assert is_valid is False
        assert "Disposable" in error


class TestUserDomainServiceValidatePasswordStrength:
    """Tests for UserDomainService.validate_password_strength method."""

    def test_strong_password(self) -> None:
        """Test strong password passes validation."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, errors = service.validate_password_strength("SecurePass123!")

        assert is_valid is True
        assert errors == []

    def test_too_short(self) -> None:
        """Test password too short fails."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, errors = service.validate_password_strength("Short1!")

        assert is_valid is False
        assert any("8 characters" in e for e in errors)

    def test_no_uppercase(self) -> None:
        """Test password without uppercase fails."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, errors = service.validate_password_strength("lowercase123!")

        assert is_valid is False
        assert any("uppercase" in e for e in errors)

    def test_no_lowercase(self) -> None:
        """Test password without lowercase fails."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, errors = service.validate_password_strength("UPPERCASE123!")

        assert is_valid is False
        assert any("lowercase" in e for e in errors)

    def test_no_digit(self) -> None:
        """Test password without digit fails."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, errors = service.validate_password_strength("NoDigitsHere!")

        assert is_valid is False
        assert any("digit" in e for e in errors)

    def test_no_special_char(self) -> None:
        """Test password without special character fails."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, errors = service.validate_password_strength("NoSpecial123")

        assert is_valid is False
        assert any("special" in e for e in errors)

    def test_weak_password_multiple_errors(self) -> None:
        """Test weak password returns multiple errors."""
        service = UserDomainService(password_hasher=MockPasswordHasher())

        is_valid, errors = service.validate_password_strength("weak")

        assert is_valid is False
        assert len(errors) >= 3
