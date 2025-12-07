"""Tests for Users DTOs commands module.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from application.users.dtos.commands import (
    ChangeEmailDTO,
    ChangePasswordDTO,
    CreateUserDTO,
    UpdateUserDTO,
    UserDTO,
    UserListDTO,
)


class TestUserDTO:
    """Tests for UserDTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating UserDTO with required fields."""
        now = datetime.now()
        dto = UserDTO(
            id="user-123",
            email="test@example.com",
            created_at=now,
            updated_at=now,
        )
        assert dto.id == "user-123"
        assert dto.email == "test@example.com"
        assert dto.is_active is True
        assert dto.is_verified is False

    def test_create_with_all_fields(self) -> None:
        """Test creating UserDTO with all fields."""
        now = datetime.now()
        dto = UserDTO(
            id="user-456",
            email="full@example.com",
            username="fulluser",
            display_name="Full User",
            is_active=False,
            is_verified=True,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )
        assert dto.username == "fulluser"
        assert dto.display_name == "Full User"
        assert dto.is_active is False
        assert dto.is_verified is True
        assert dto.last_login_at == now

    def test_frozen_model(self) -> None:
        """Test that UserDTO is immutable."""
        now = datetime.now()
        dto = UserDTO(
            id="user-123",
            email="test@example.com",
            created_at=now,
            updated_at=now,
        )
        with pytest.raises(ValidationError):
            dto.email = "new@example.com"


class TestCreateUserDTO:
    """Tests for CreateUserDTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating with required fields."""
        dto = CreateUserDTO(
            email="test@example.com",
            password="securepassword123",
        )
        assert dto.email == "test@example.com"
        assert dto.password == "securepassword123"
        assert dto.username is None
        assert dto.display_name is None

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        dto = CreateUserDTO(
            email="full@example.com",
            password="securepassword123",
            username="fulluser",
            display_name="Full User",
        )
        assert dto.username == "fulluser"
        assert dto.display_name == "Full User"

    def test_email_validation_lowercase(self) -> None:
        """Test that email is converted to lowercase."""
        dto = CreateUserDTO(
            email="TEST@EXAMPLE.COM",
            password="securepassword123",
        )
        assert dto.email == "test@example.com"

    def test_invalid_email_raises(self) -> None:
        """Test that invalid email raises ValidationError."""
        with pytest.raises(ValidationError):
            CreateUserDTO(
                email="invalid-email",
                password="securepassword123",
            )

    def test_short_password_raises(self) -> None:
        """Test that short password raises ValidationError."""
        with pytest.raises(ValidationError):
            CreateUserDTO(
                email="test@example.com",
                password="short",
            )

    def test_short_email_raises(self) -> None:
        """Test that short email raises ValidationError."""
        with pytest.raises(ValidationError):
            CreateUserDTO(
                email="a@b",
                password="securepassword123",
            )

    def test_short_username_raises(self) -> None:
        """Test that short username raises ValidationError."""
        with pytest.raises(ValidationError):
            CreateUserDTO(
                email="test@example.com",
                password="securepassword123",
                username="ab",
            )


class TestUpdateUserDTO:
    """Tests for UpdateUserDTO."""

    def test_empty_update(self) -> None:
        """Test creating empty update DTO."""
        dto = UpdateUserDTO()
        assert dto.username is None
        assert dto.display_name is None

    def test_partial_update(self) -> None:
        """Test partial update with some fields."""
        dto = UpdateUserDTO(username="newusername")
        assert dto.username == "newusername"
        assert dto.display_name is None

    def test_full_update(self) -> None:
        """Test full update with all fields."""
        dto = UpdateUserDTO(
            username="newusername",
            display_name="New Display Name",
        )
        assert dto.username == "newusername"
        assert dto.display_name == "New Display Name"

    def test_short_username_raises(self) -> None:
        """Test that short username raises ValidationError."""
        with pytest.raises(ValidationError):
            UpdateUserDTO(username="ab")


class TestChangePasswordDTO:
    """Tests for ChangePasswordDTO."""

    def test_create_with_valid_data(self) -> None:
        """Test creating with valid data."""
        dto = ChangePasswordDTO(
            current_password="oldpassword123",
            new_password="newpassword456",
        )
        assert dto.current_password == "oldpassword123"
        assert dto.new_password == "newpassword456"

    def test_short_new_password_raises(self) -> None:
        """Test that short new password raises ValidationError."""
        with pytest.raises(ValidationError):
            ChangePasswordDTO(
                current_password="oldpassword123",
                new_password="short",
            )


class TestChangeEmailDTO:
    """Tests for ChangeEmailDTO."""

    def test_create_with_valid_data(self) -> None:
        """Test creating with valid data."""
        dto = ChangeEmailDTO(
            new_email="new@example.com",
            password="currentpassword",
        )
        assert dto.new_email == "new@example.com"
        assert dto.password == "currentpassword"

    def test_email_validation_lowercase(self) -> None:
        """Test that email is converted to lowercase."""
        dto = ChangeEmailDTO(
            new_email="NEW@EXAMPLE.COM",
            password="currentpassword",
        )
        assert dto.new_email == "new@example.com"

    def test_invalid_email_raises(self) -> None:
        """Test that invalid email raises ValidationError."""
        with pytest.raises(ValidationError):
            ChangeEmailDTO(
                new_email="invalid-email",
                password="currentpassword",
            )


class TestUserListDTO:
    """Tests for UserListDTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating with required fields."""
        now = datetime.now()
        dto = UserListDTO(
            id="user-123",
            email="test@example.com",
            created_at=now,
        )
        assert dto.id == "user-123"
        assert dto.email == "test@example.com"
        assert dto.is_active is True

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        now = datetime.now()
        dto = UserListDTO(
            id="user-456",
            email="full@example.com",
            username="fulluser",
            display_name="Full User",
            is_active=False,
            created_at=now,
        )
        assert dto.username == "fulluser"
        assert dto.display_name == "Full User"
        assert dto.is_active is False
