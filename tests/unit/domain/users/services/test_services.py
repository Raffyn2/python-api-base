"""Tests for user domain services.

Tests UserDomainService with password hashing and email validation.
"""

import pytest

from domain.users.services import UserDomainService


class MockPasswordHasher:
    """Mock password hasher for testing."""

    def hash(self, password: str) -> str:
        return f"hashed_{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed_{password}"


class MockEmailValidator:
    """Mock email validator for testing."""

    def __init__(self, disposable_domains: list[str] | None = None) -> None:
        self._disposable = disposable_domains or ["tempmail.com", "10minutemail.com"]

    def is_valid(self, email: str) -> bool:
        return "@" in email and "." in email.split("@")[-1]

    def is_disposable(self, email: str) -> bool:
        if "@" not in email:
            return False
        domain = email.split("@")[1]
        return domain in self._disposable


class TestUserDomainServicePasswordHashing:
    """Tests for password hashing functionality."""

    @pytest.fixture()
    def service(self) -> UserDomainService:
        return UserDomainService(password_hasher=MockPasswordHasher())

    def test_hash_password(self, service: UserDomainService) -> None:
        result = service.hash_password("MyPassword123!")
        assert result == "hashed_MyPassword123!"

    def test_verify_password_correct(self, service: UserDomainService) -> None:
        hashed = service.hash_password("MyPassword123!")
        assert service.verify_password("MyPassword123!", hashed) is True

    def test_verify_password_incorrect(self, service: UserDomainService) -> None:
        hashed = service.hash_password("MyPassword123!")
        assert service.verify_password("WrongPassword", hashed) is False


class TestUserDomainServiceEmailValidation:
    """Tests for email validation functionality."""

    def test_basic_email_validation_valid(self) -> None:
        service = UserDomainService(password_hasher=MockPasswordHasher())
        is_valid, error = service.validate_email("user@example.com")
        assert is_valid is True
        assert error is None

    def test_basic_email_validation_invalid(self) -> None:
        service = UserDomainService(password_hasher=MockPasswordHasher())
        is_valid, error = service.validate_email("not-an-email")
        assert is_valid is False
        assert error == "Invalid email format"

    def test_basic_email_validation_no_at(self) -> None:
        service = UserDomainService(password_hasher=MockPasswordHasher())
        is_valid, _error = service.validate_email("userexample.com")
        assert is_valid is False

    def test_basic_email_validation_no_domain(self) -> None:
        service = UserDomainService(password_hasher=MockPasswordHasher())
        is_valid, _error = service.validate_email("user@")
        assert is_valid is False

    def test_with_validator_valid_email(self) -> None:
        service = UserDomainService(
            password_hasher=MockPasswordHasher(),
            email_validator=MockEmailValidator(),
        )
        is_valid, error = service.validate_email("user@example.com")
        assert is_valid is True
        assert error is None

    def test_with_validator_invalid_email(self) -> None:
        service = UserDomainService(
            password_hasher=MockPasswordHasher(),
            email_validator=MockEmailValidator(),
        )
        is_valid, error = service.validate_email("invalid")
        assert is_valid is False
        assert error == "Invalid email format"

    def test_with_validator_disposable_email(self) -> None:
        service = UserDomainService(
            password_hasher=MockPasswordHasher(),
            email_validator=MockEmailValidator(),
        )
        is_valid, error = service.validate_email("user@tempmail.com")
        assert is_valid is False
        assert error == "Disposable email addresses are not allowed"


class TestUserDomainServicePasswordStrength:
    """Tests for password strength validation."""

    @pytest.fixture()
    def service(self) -> UserDomainService:
        return UserDomainService(password_hasher=MockPasswordHasher())

    def test_strong_password(self, service: UserDomainService) -> None:
        is_valid, errors = service.validate_password_strength("SecurePass123!")
        assert is_valid is True
        assert errors == []

    def test_too_short(self, service: UserDomainService) -> None:
        is_valid, errors = service.validate_password_strength("Aa1!")
        assert is_valid is False
        assert "Password must be at least 8 characters" in errors

    def test_no_uppercase(self, service: UserDomainService) -> None:
        is_valid, errors = service.validate_password_strength("securepass123!")
        assert is_valid is False
        assert "Password must contain at least one uppercase letter" in errors

    def test_no_lowercase(self, service: UserDomainService) -> None:
        is_valid, errors = service.validate_password_strength("SECUREPASS123!")
        assert is_valid is False
        assert "Password must contain at least one lowercase letter" in errors

    def test_no_digit(self, service: UserDomainService) -> None:
        is_valid, errors = service.validate_password_strength("SecurePass!")
        assert is_valid is False
        assert "Password must contain at least one digit" in errors

    def test_no_special_char(self, service: UserDomainService) -> None:
        is_valid, errors = service.validate_password_strength("SecurePass123")
        assert is_valid is False
        assert "Password must contain at least one special character" in errors

    def test_multiple_errors(self, service: UserDomainService) -> None:
        is_valid, errors = service.validate_password_strength("weak")
        assert is_valid is False
        assert len(errors) >= 3  # At least: too short, no uppercase, no digit, no special

    def test_all_special_chars_accepted(self, service: UserDomainService) -> None:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for char in special_chars:
            password = f"SecurePass1{char}"
            is_valid, _errors = service.validate_password_strength(password)
            assert is_valid is True, f"Special char '{char}' should be accepted"
