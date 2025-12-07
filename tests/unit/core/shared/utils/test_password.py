"""Unit tests for password utilities.

Tests password hashing and verification.
"""

import pytest

from core.shared.utils.password import hash_password, needs_rehash, verify_password


class TestHashPassword:
    """Tests for hash_password function."""

    def test_returns_string(self) -> None:
        """Test returns string hash."""
        result = hash_password("SecurePassword123!")
        assert isinstance(result, str)

    def test_hash_is_not_plaintext(self) -> None:
        """Test hash is not the plaintext password."""
        password = "SecurePassword123!"
        result = hash_password(password)
        assert result != password

    def test_different_hashes_for_same_password(self) -> None:
        """Test same password produces different hashes (salted)."""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_empty_password_raises(self) -> None:
        """Test empty password raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            hash_password("")

    def test_hash_contains_argon2(self) -> None:
        """Test hash contains argon2 identifier."""
        result = hash_password("SecurePassword123!")
        assert "argon2" in result


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_correct_password_returns_true(self) -> None:
        """Test correct password returns True."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_wrong_password_returns_false(self) -> None:
        """Test wrong password returns False."""
        hashed = hash_password("SecurePassword123!")

        result = verify_password("WrongPassword!", hashed)

        assert result is False

    def test_empty_password_returns_false(self) -> None:
        """Test empty password returns False."""
        hashed = hash_password("SecurePassword123!")

        result = verify_password("", hashed)

        assert result is False

    def test_empty_hash_returns_false(self) -> None:
        """Test empty hash returns False."""
        result = verify_password("password", "")
        assert result is False

    def test_invalid_hash_returns_false(self) -> None:
        """Test invalid hash returns False."""
        result = verify_password("password", "invalid_hash")
        assert result is False


class TestNeedsRehash:
    """Tests for needs_rehash function."""

    def test_valid_hash_no_rehash(self) -> None:
        """Test valid hash doesn't need rehash."""
        hashed = hash_password("SecurePassword123!")

        result = needs_rehash(hashed)

        assert result is False

    def test_empty_hash_needs_rehash(self) -> None:
        """Test empty hash needs rehash."""
        result = needs_rehash("")
        assert result is True

    def test_invalid_hash_needs_rehash(self) -> None:
        """Test invalid hash needs rehash."""
        result = needs_rehash("invalid_hash")
        assert result is True
