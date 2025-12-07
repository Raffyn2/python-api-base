"""Unit tests for user value objects.

Tests Email, PasswordHash, UserId, Username, and PhoneNumber.
"""

import pytest

from domain.users.value_objects import (
    Email,
    PasswordHash,
    PhoneNumber,
    UserId,
    Username,
)


class TestEmail:
    """Tests for Email value object."""

    def test_valid_email(self) -> None:
        """Test valid email creation."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"

    def test_normalizes_to_lowercase(self) -> None:
        """Test email is normalized to lowercase."""
        email = Email("Test@EXAMPLE.COM")
        assert email.value == "test@example.com"

    def test_valid_email_with_subdomain(self) -> None:
        """Test valid email with subdomain."""
        email = Email("test@mail.example.com")
        assert email.value == "test@mail.example.com"

    def test_invalid_format_raises(self) -> None:
        """Test invalid email format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")

    def test_missing_at_raises(self) -> None:
        """Test email without @ raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("testexample.com")

    def test_missing_domain_raises(self) -> None:
        """Test email without domain raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            Email("test@")

    def test_create_factory(self) -> None:
        """Test create factory method."""
        email = Email.create("user@domain.org")
        assert email.value == "user@domain.org"

    def test_str_representation(self) -> None:
        """Test string representation."""
        email = Email("test@example.com")
        assert str(email) == "test@example.com"


class TestPasswordHash:
    """Tests for PasswordHash value object."""

    def test_valid_hash(self) -> None:
        """Test valid password hash creation."""
        ph = PasswordHash("$argon2id$v=19$m=65536,t=3,p=4$hash")
        assert ph.value == "$argon2id$v=19$m=65536,t=3,p=4$hash"
        assert ph.algorithm == "argon2id"

    def test_custom_algorithm(self) -> None:
        """Test password hash with custom algorithm."""
        ph = PasswordHash("bcrypt_hash", algorithm="bcrypt")
        assert ph.algorithm == "bcrypt"

    def test_empty_hash_raises(self) -> None:
        """Test empty hash raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            PasswordHash("")

    def test_create_factory(self) -> None:
        """Test create factory method."""
        ph = PasswordHash.create("hash_value", "scrypt")
        assert ph.value == "hash_value"
        assert ph.algorithm == "scrypt"

    def test_str_hides_value(self) -> None:
        """Test string representation hides actual hash."""
        ph = PasswordHash("secret_hash")
        assert str(ph) == "[HASHED:argon2id]"
        assert "secret_hash" not in str(ph)


class TestUserId:
    """Tests for UserId value object."""

    def test_valid_user_id(self) -> None:
        """Test valid user ID creation."""
        uid = UserId("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert uid.value == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_empty_raises(self) -> None:
        """Test empty user ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            UserId("")

    def test_whitespace_only_raises(self) -> None:
        """Test whitespace-only user ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            UserId("   ")

    def test_create_factory(self) -> None:
        """Test create factory method."""
        uid = UserId.create("user-123")
        assert uid.value == "user-123"

    def test_str_representation(self) -> None:
        """Test string representation."""
        uid = UserId("user-456")
        assert str(uid) == "user-456"


class TestUsername:
    """Tests for Username value object."""

    def test_valid_username(self) -> None:
        """Test valid username creation."""
        username = Username("john_doe")
        assert username.value == "john_doe"

    def test_with_hyphen(self) -> None:
        """Test username with hyphen."""
        username = Username("john-doe")
        assert username.value == "john-doe"

    def test_with_numbers(self) -> None:
        """Test username with numbers."""
        username = Username("user123")
        assert username.value == "user123"

    def test_too_short_raises(self) -> None:
        """Test username too short raises ValueError."""
        with pytest.raises(ValueError, match="at least 3 characters"):
            Username("ab")

    def test_too_long_raises(self) -> None:
        """Test username too long raises ValueError."""
        with pytest.raises(ValueError, match="at most 50 characters"):
            Username("a" * 51)

    def test_invalid_characters_raises(self) -> None:
        """Test invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="can only contain"):
            Username("john@doe")

    def test_spaces_raises(self) -> None:
        """Test spaces raise ValueError."""
        with pytest.raises(ValueError, match="can only contain"):
            Username("john doe")

    def test_create_factory(self) -> None:
        """Test create factory method."""
        username = Username.create("jane_doe")
        assert username.value == "jane_doe"

    def test_str_representation(self) -> None:
        """Test string representation."""
        username = Username("test_user")
        assert str(username) == "test_user"


class TestPhoneNumber:
    """Tests for PhoneNumber value object."""

    def test_valid_phone(self) -> None:
        """Test valid phone number creation."""
        phone = PhoneNumber("1234567890")
        assert phone.value == "1234567890"

    def test_with_formatting(self) -> None:
        """Test phone number with formatting."""
        phone = PhoneNumber("(123) 456-7890")
        assert phone.value == "(123) 456-7890"

    def test_with_country_code(self) -> None:
        """Test phone number with country code."""
        phone = PhoneNumber("1234567890", country_code="1")
        assert phone.country_code == "1"

    def test_too_short_raises(self) -> None:
        """Test phone number too short raises ValueError."""
        with pytest.raises(ValueError, match="10-15 digits"):
            PhoneNumber("123456789")

    def test_too_long_raises(self) -> None:
        """Test phone number too long raises ValueError."""
        with pytest.raises(ValueError, match="10-15 digits"):
            PhoneNumber("1234567890123456")

    def test_create_factory(self) -> None:
        """Test create factory method."""
        phone = PhoneNumber.create("9876543210", "55")
        assert phone.value == "9876543210"
        assert phone.country_code == "55"

    def test_str_without_country_code(self) -> None:
        """Test string representation without country code."""
        phone = PhoneNumber("1234567890")
        assert str(phone) == "1234567890"

    def test_str_with_country_code(self) -> None:
        """Test string representation with country code."""
        phone = PhoneNumber("1234567890", country_code="1")
        assert str(phone) == "+1 1234567890"
