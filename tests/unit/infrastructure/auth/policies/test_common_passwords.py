"""Tests for common passwords module."""

import pytest

from infrastructure.auth.policies.common_passwords import COMMON_PASSWORDS


class TestCommonPasswords:
    """Tests for COMMON_PASSWORDS constant."""

    def test_is_frozenset(self) -> None:
        assert isinstance(COMMON_PASSWORDS, frozenset)

    def test_is_not_empty(self) -> None:
        assert len(COMMON_PASSWORDS) > 0

    def test_contains_password(self) -> None:
        assert "password" in COMMON_PASSWORDS

    def test_contains_123456(self) -> None:
        assert "123456" in COMMON_PASSWORDS

    def test_contains_qwerty(self) -> None:
        assert "qwerty" in COMMON_PASSWORDS

    def test_contains_admin(self) -> None:
        assert "admin" in COMMON_PASSWORDS

    def test_contains_letmein(self) -> None:
        assert "letmein" in COMMON_PASSWORDS

    def test_contains_welcome(self) -> None:
        assert "welcome" in COMMON_PASSWORDS

    def test_contains_iloveyou(self) -> None:
        assert "iloveyou" in COMMON_PASSWORDS

    def test_all_lowercase(self) -> None:
        for pwd in COMMON_PASSWORDS:
            assert pwd == pwd.lower(), f"Password '{pwd}' is not lowercase"

    def test_all_strings(self) -> None:
        for pwd in COMMON_PASSWORDS:
            assert isinstance(pwd, str)

    def test_no_empty_strings(self) -> None:
        for pwd in COMMON_PASSWORDS:
            assert len(pwd) > 0

    def test_immutable(self) -> None:
        with pytest.raises(AttributeError):
            COMMON_PASSWORDS.add("newpassword")  # type: ignore

    def test_has_numeric_passwords(self) -> None:
        numeric = [p for p in COMMON_PASSWORDS if p.isdigit()]
        assert len(numeric) > 0

    def test_has_common_words(self) -> None:
        common_words = ["dragon", "master", "sunshine", "princess"]
        for word in common_words:
            assert word in COMMON_PASSWORDS
