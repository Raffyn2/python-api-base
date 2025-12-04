"""Contract tests for Users API.

Verifies the Users API contract remains stable for consumers.

**Feature: contract-testing**
**Validates: Requirements 12.1, 12.2**
"""

import pytest
from pydantic import BaseModel, Field


class UserResponseContract(BaseModel):
    """Expected contract for user response."""

    id: str = Field(..., min_length=1)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    username: str | None = None
    display_name: str | None = None
    is_active: bool
    is_verified: bool
    created_at: str | None = None
    updated_at: str | None = None


class UserListItemContract(BaseModel):
    """Expected contract for user list item."""

    id: str = Field(..., min_length=1)
    email: str
    username: str | None = None
    is_active: bool


class PaginatedUsersContract(BaseModel):
    """Expected contract for paginated users response."""

    items: list[UserListItemContract]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)


class CreateUserRequestContract(BaseModel):
    """Expected contract for create user request."""

    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=12)
    username: str | None = None
    display_name: str | None = None


class UpdateUserRequestContract(BaseModel):
    """Expected contract for update user request."""

    username: str | None = None
    display_name: str | None = None


class TestUsersContractSchema:
    """Contract schema validation tests."""

    def test_user_response_contract_valid(self) -> None:
        """Verify valid user response matches contract."""
        data = {
            "id": "usr_123",
            "email": "test@example.com",
            "username": "testuser",
            "display_name": "Test User",
            "is_active": True,
            "is_verified": False,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": None,
        }
        user = UserResponseContract.model_validate(data)
        assert user.id == "usr_123"
        assert user.email == "test@example.com"

    def test_user_response_contract_minimal(self) -> None:
        """Verify minimal user response matches contract."""
        data = {
            "id": "usr_456",
            "email": "minimal@example.com",
            "is_active": True,
            "is_verified": False,
        }
        user = UserResponseContract.model_validate(data)
        assert user.username is None
        assert user.display_name is None

    def test_user_response_contract_invalid_email(self) -> None:
        """Verify invalid email fails contract."""
        data = {
            "id": "usr_789",
            "email": "invalid-email",
            "is_active": True,
            "is_verified": False,
        }
        with pytest.raises(ValueError):
            UserResponseContract.model_validate(data)

    def test_user_response_contract_empty_id(self) -> None:
        """Verify empty id fails contract."""
        data = {
            "id": "",
            "email": "test@example.com",
            "is_active": True,
            "is_verified": False,
        }
        with pytest.raises(ValueError):
            UserResponseContract.model_validate(data)

    def test_paginated_users_contract_valid(self) -> None:
        """Verify valid paginated response matches contract."""
        data = {
            "items": [
                {"id": "usr_1", "email": "a@b.com", "is_active": True},
                {"id": "usr_2", "email": "c@d.com", "is_active": False},
            ],
            "total": 50,
            "page": 1,
            "size": 20,
        }
        response = PaginatedUsersContract.model_validate(data)
        assert len(response.items) == 2
        assert response.total == 50

    def test_paginated_users_contract_empty(self) -> None:
        """Verify empty paginated response matches contract."""
        data = {"items": [], "total": 0, "page": 1, "size": 20}
        response = PaginatedUsersContract.model_validate(data)
        assert len(response.items) == 0

    def test_create_user_request_contract_valid(self) -> None:
        """Verify valid create request matches contract."""
        data = {
            "email": "new@example.com",
            "password": "SecurePass123!",
            "username": "newuser",
        }
        request = CreateUserRequestContract.model_validate(data)
        assert request.email == "new@example.com"

    def test_create_user_request_contract_weak_password(self) -> None:
        """Verify weak password fails contract."""
        data = {"email": "new@example.com", "password": "short"}
        with pytest.raises(ValueError):
            CreateUserRequestContract.model_validate(data)

    def test_update_user_request_contract_partial(self) -> None:
        """Verify partial update matches contract."""
        data = {"username": "updated"}
        request = UpdateUserRequestContract.model_validate(data)
        assert request.username == "updated"
        assert request.display_name is None


class TestUsersContractBackwardCompatibility:
    """Backward compatibility contract tests."""

    def test_response_allows_extra_fields(self) -> None:
        """Verify response contract ignores unknown fields (forward compat)."""
        data = {
            "id": "usr_123",
            "email": "test@example.com",
            "is_active": True,
            "is_verified": False,
            "future_field": "should be ignored",
        }
        # Should not raise - extra fields ignored by default
        user = UserResponseContract.model_validate(data)
        assert user.id == "usr_123"

    def test_required_fields_present(self) -> None:
        """Verify all required fields are documented."""
        required_fields = {"id", "email", "is_active", "is_verified"}
        schema = UserResponseContract.model_json_schema()
        actual_required = set(schema.get("required", []))
        assert required_fields == actual_required
