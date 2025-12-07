"""Tests for Users Read Model DTOs.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

from datetime import datetime

import pytest

from application.users.dtos.read_model import (
    UserActivityReadDTO,
    UserListReadDTO,
    UserReadDTO,
    UserSearchResultDTO,
)


class TestUserReadDTO:
    """Tests for UserReadDTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating with required fields."""
        dto = UserReadDTO(id="user-123", email="test@example.com")
        assert dto.id == "user-123"
        assert dto.email == "test@example.com"
        assert dto.is_active is True
        assert dto.is_verified is False
        assert dto.role_names == ()
        assert dto.permission_count == 0

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        now = datetime.now()
        dto = UserReadDTO(
            id="user-456",
            email="full@example.com",
            username="fulluser",
            display_name="Full User",
            is_active=False,
            is_verified=True,
            created_at=now,
            updated_at=now,
            last_login_at=now,
            role_names=("admin", "user"),
            permission_count=10,
        )
        assert dto.username == "fulluser"
        assert dto.display_name == "Full User"
        assert dto.is_active is False
        assert dto.is_verified is True
        assert dto.role_names == ("admin", "user")
        assert dto.permission_count == 10

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        now = datetime.now()
        dto = UserReadDTO(
            id="user-123",
            email="test@example.com",
            username="testuser",
            created_at=now,
            role_names=("user",),
        )
        result = dto.to_dict()
        assert result["id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert result["created_at"] == now.isoformat()
        assert result["role_names"] == ["user"]

    def test_to_dict_with_none_dates(self) -> None:
        """Test to_dict with None dates."""
        dto = UserReadDTO(id="user-123", email="test@example.com")
        result = dto.to_dict()
        assert result["created_at"] is None
        assert result["updated_at"] is None
        assert result["last_login_at"] is None

    def test_frozen_dataclass(self) -> None:
        """Test that UserReadDTO is immutable."""
        dto = UserReadDTO(id="user-123", email="test@example.com")
        with pytest.raises(AttributeError):
            dto.email = "new@example.com"


class TestUserListReadDTO:
    """Tests for UserListReadDTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating with required fields."""
        dto = UserListReadDTO(id="user-123", email="test@example.com")
        assert dto.id == "user-123"
        assert dto.email == "test@example.com"
        assert dto.is_active is True

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        now = datetime.now()
        dto = UserListReadDTO(
            id="user-456",
            email="full@example.com",
            display_name="Full User",
            is_active=False,
            created_at=now,
        )
        assert dto.display_name == "Full User"
        assert dto.is_active is False
        assert dto.created_at == now

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        now = datetime.now()
        dto = UserListReadDTO(
            id="user-123",
            email="test@example.com",
            display_name="Test User",
            created_at=now,
        )
        result = dto.to_dict()
        assert result["id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["display_name"] == "Test User"
        assert result["created_at"] == now.isoformat()

    def test_to_dict_with_none_date(self) -> None:
        """Test to_dict with None created_at."""
        dto = UserListReadDTO(id="user-123", email="test@example.com")
        result = dto.to_dict()
        assert result["created_at"] is None


class TestUserSearchResultDTO:
    """Tests for UserSearchResultDTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating with required fields."""
        dto = UserSearchResultDTO(id="user-123", email="test@example.com")
        assert dto.id == "user-123"
        assert dto.email == "test@example.com"
        assert dto.relevance_score == 0.0
        assert dto.matched_fields == ()

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        dto = UserSearchResultDTO(
            id="user-456",
            email="search@example.com",
            display_name="Search User",
            relevance_score=0.95,
            matched_fields=("email", "display_name"),
        )
        assert dto.display_name == "Search User"
        assert dto.relevance_score == 0.95
        assert dto.matched_fields == ("email", "display_name")

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        dto = UserSearchResultDTO(
            id="user-123",
            email="test@example.com",
            relevance_score=0.85,
            matched_fields=("email",),
        )
        result = dto.to_dict()
        assert result["id"] == "user-123"
        assert result["relevance_score"] == 0.85
        assert result["matched_fields"] == ["email"]


class TestUserActivityReadDTO:
    """Tests for UserActivityReadDTO."""

    def test_create_with_required_fields(self) -> None:
        """Test creating with required fields."""
        dto = UserActivityReadDTO(user_id="user-123")
        assert dto.user_id == "user-123"
        assert dto.total_logins == 0
        assert dto.active_sessions == 0

    def test_create_with_all_fields(self) -> None:
        """Test creating with all fields."""
        now = datetime.now()
        dto = UserActivityReadDTO(
            user_id="user-456",
            total_logins=100,
            last_login_at=now,
            last_activity_at=now,
            active_sessions=3,
        )
        assert dto.total_logins == 100
        assert dto.last_login_at == now
        assert dto.last_activity_at == now
        assert dto.active_sessions == 3

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        now = datetime.now()
        dto = UserActivityReadDTO(
            user_id="user-123",
            total_logins=50,
            last_login_at=now,
            active_sessions=2,
        )
        result = dto.to_dict()
        assert result["user_id"] == "user-123"
        assert result["total_logins"] == 50
        assert result["last_login_at"] == now.isoformat()
        assert result["active_sessions"] == 2

    def test_to_dict_with_none_dates(self) -> None:
        """Test to_dict with None dates."""
        dto = UserActivityReadDTO(user_id="user-123")
        result = dto.to_dict()
        assert result["last_login_at"] is None
        assert result["last_activity_at"] is None
