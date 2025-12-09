"""Unit tests for domain/users/value_objects/value_objects.py.

Tests user-specific value objects.

**Task 8.2: Create tests for user value objects**
**Requirements: 2.2**
"""

import pytest

from domain.users.value_objects.value_objects import (
    Email,
    PasswordHash,
    PhoneNumber,
    UserId,
    Username,
)


class TestEmail:
    """Tests for Email value object."""

    def test_create_valid_email(self) -> None:
        """Test creating valid email."""
        email = Email.create("test@example.com")
        assert email.value == "test@example.com"

    def test_normalizes_to_lowercase(self) -> None:
        """Test email is normalized to lowercase."""
        email = Email.create("Test@Example.COM")
        assert email.value == "test@example.com"

    def test_normalizes_case(self) -> None:
        """Test email is normalized to lowercase."""
        email = Email.create("TEST@EXAMPLE.COM")
        assert email.value == "test@example.com"

    def test_invalid_email_raises(self) -> None:
        """Test invalid email raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email"):
            Email.create("invalid-email")

    def test_email_without_domain_raises(self) -> None:
        """Test email without domain raises ValueError."""
        with pytest.raises(ValueError):
            Email.create("test@")

    def test_str_representation(self) -> None:
        """Test string representation."""
        email = Email.create("test@example.com")
        assert str(email) == "test@example.com"

    def test_immutability(self) -> None:
        """Test email is immutable."""
        email = Email.create("test@example.com")
        with pytest.raises(AttributeError):
            email.value = "new@example.com"


class TestPasswordHash:
    """Tests for PasswordHash value object."""

    def test_create_valid_hash(self) -> None:
        """Test creating valid password hash."""
        ph = PasswordHash.create("$argon2id$v=19$hash")
        assert ph.value == "$argon2id$v=19$hash"
        assert ph.algorithm == "argon2id"

    def test_custom_algorithm(self) -> None:
        """Test custom algorithm."""
        ph = PasswordHash.create("bcrypt_hash", algorithm="bcrypt")
        assert ph.algorithm == "bcrypt"

    def test_empty_hash_raises(self) -> None:
        """Test empty hash raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            PasswordHash.create("")

    def test_str_hides_value(self) -> None:
        """Test string representation hides actual hash."""
        ph = PasswordHash.create("secret_hash")
        assert "secret_hash" not in str(ph)
        assert "HASHED" in str(ph)


class TestUserId:
    """Tests for UserId value object."""

    def test_create_valid_id(self) -> None:
        """Test creating valid user ID."""
        uid = UserId.create("user-123")
        assert uid.value == "user-123"

    def test_empty_id_raises(self) -> None:
        """Test empty ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            UserId.create("")

    def test_whitespace_only_raises(self) -> None:
        """Test whitespace-only ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            UserId.create("   ")

    def test_str_representation(self) -> None:
        """Test string representation."""
        uid = UserId.create("user-123")
        assert str(uid) == "user-123"


class TestUsername:
    """Tests for Username value object."""

    def test_create_valid_username(self) -> None:
        """Test creating valid username."""
        username = Username.create("testuser")
        assert username.value == "testuser"

    def test_username_with_numbers(self) -> None:
        """Test username with numbers."""
        username = Username.create("user123")
        assert username.value == "user123"

    def test_username_with_underscore(self) -> None:
        """Test username with underscore."""
        username = Username.create("test_user")
        assert username.value == "test_user"

    def test_username_with_hyphen(self) -> None:
        """Test username with hyphen."""
        username = Username.create("test-user")
        assert username.value == "test-user"

    def test_too_short_raises(self) -> None:
        """Test username too short raises ValueError."""
        with pytest.raises(ValueError, match="at least"):
            Username.create("ab")

    def test_too_long_raises(self) -> None:
        """Test username too long raises ValueError."""
        with pytest.raises(ValueError, match="at most"):
            Username.create("a" * 51)

    def test_invalid_characters_raises(self) -> None:
        """Test invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="only contain"):
            Username.create("test@user")

        with pytest.raises(ValueError):
            Username.create("test user")


class TestPhoneNumber:
    """Tests for PhoneNumber value object."""

    def test_create_valid_phone(self) -> None:
        """Test creating valid phone number."""
        phone = PhoneNumber.create("1234567890")
        assert phone.value == "1234567890"

    def test_with_country_code(self) -> None:
        """Test phone with country code."""
        phone = PhoneNumber.create("+1234567890", country_code="1")
        assert phone.country_code == "1"

    def test_too_short_raises(self) -> None:
        """Test phone too short raises ValueError."""
        with pytest.raises(ValueError, match="10-15 digits"):
            PhoneNumber.create("123456789")

    def test_too_long_raises(self) -> None:
        """Test phone too long raises ValueError."""
        with pytest.raises(ValueError, match="10-15 digits"):
            PhoneNumber.create("1234567890123456")

    def test_str_with_country_code(self) -> None:
        """Test string representation with country code."""
        phone = PhoneNumber.create("1234567890", country_code="1")
        assert "+1" in str(phone)
