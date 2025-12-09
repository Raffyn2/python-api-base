"""Unit tests for UserMapper.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.3**
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from application.users.dtos import UserDTO, UserListDTO
from application.users.mappers.commands import UserMapper
from domain.users.aggregates import UserAggregate


class TestUserMapperToDto:
    """Tests for to_dto method."""

    @pytest.fixture
    def mapper(self) -> UserMapper:
        """Create mapper instance."""
        return UserMapper()

    @pytest.fixture
    def sample_aggregate(self) -> UserAggregate:
        """Create sample user aggregate."""
        return UserAggregate(
            id="user-123",
            email="test@example.com",
            password_hash="hashed_password",
            username="testuser",
            display_name="Test User",
            is_active=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 2, tzinfo=UTC),
            last_login_at=datetime(2024, 1, 3, tzinfo=UTC),
        )

    def test_to_dto_success(self, mapper: UserMapper, sample_aggregate: UserAggregate) -> None:
        """Should convert aggregate to DTO."""
        dto = mapper.to_dto(sample_aggregate)

        assert dto.id == "user-123"
        assert dto.email == "test@example.com"
        assert dto.username == "testuser"
        assert dto.display_name == "Test User"
        assert dto.is_active is True
        assert dto.is_verified is True

    def test_to_dto_none_raises(self, mapper: UserMapper) -> None:
        """Should raise ValueError for None aggregate."""
        with pytest.raises(ValueError, match="cannot be None"):
            mapper.to_dto(None)  # type: ignore

    def test_to_dto_wrong_type_raises(self, mapper: UserMapper) -> None:
        """Should raise TypeError for wrong type."""
        with pytest.raises(TypeError, match="Expected UserAggregate"):
            mapper.to_dto("not an aggregate")  # type: ignore


class TestUserMapperToEntity:
    """Tests for to_entity method."""

    @pytest.fixture
    def mapper(self) -> UserMapper:
        """Create mapper instance."""
        return UserMapper()

    @pytest.fixture
    def sample_dto(self) -> UserDTO:
        """Create sample user DTO."""
        return UserDTO(
            id="user-123",
            email="test@example.com",
            username="testuser",
            display_name="Test User",
            is_active=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 2, tzinfo=UTC),
            last_login_at=datetime(2024, 1, 3, tzinfo=UTC),
        )

    def test_to_entity_with_password_hash(self, mapper: UserMapper, sample_dto: UserDTO) -> None:
        """Should convert DTO to aggregate with password hash."""
        aggregate = mapper.to_entity(sample_dto, password_hash="hashed_password")

        assert aggregate.id == "user-123"
        assert aggregate.email == "test@example.com"
        assert aggregate.password_hash == "hashed_password"

    def test_to_entity_without_password_hash(self, mapper: UserMapper, sample_dto: UserDTO) -> None:
        """Should convert DTO to aggregate without password hash."""
        aggregate = mapper.to_entity(sample_dto)

        assert aggregate.id == "user-123"
        assert aggregate.password_hash == ""

    def test_to_entity_none_raises(self, mapper: UserMapper) -> None:
        """Should raise ValueError for None DTO."""
        with pytest.raises(ValueError, match="cannot be None"):
            mapper.to_entity(None)  # type: ignore

    def test_to_entity_wrong_type_raises(self, mapper: UserMapper) -> None:
        """Should raise TypeError for wrong type."""
        with pytest.raises(TypeError, match="Expected UserDTO"):
            mapper.to_entity("not a dto")  # type: ignore


class TestUserMapperToListDto:
    """Tests for to_list_dto method."""

    @pytest.fixture
    def mapper(self) -> UserMapper:
        """Create mapper instance."""
        return UserMapper()

    @pytest.fixture
    def sample_aggregate(self) -> UserAggregate:
        """Create sample user aggregate."""
        return UserAggregate(
            id="user-123",
            email="test@example.com",
            password_hash="hashed_password",
            username="testuser",
            display_name="Test User",
            is_active=True,
            is_verified=True,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 2, tzinfo=UTC),
        )

    def test_to_list_dto_success(self, mapper: UserMapper, sample_aggregate: UserAggregate) -> None:
        """Should convert aggregate to list DTO."""
        dto = mapper.to_list_dto(sample_aggregate)

        assert dto.id == "user-123"
        assert dto.email == "test@example.com"
        assert dto.username == "testuser"
        assert dto.display_name == "Test User"
        assert dto.is_active is True

    def test_to_list_dto_none_raises(self, mapper: UserMapper) -> None:
        """Should raise ValueError for None aggregate."""
        with pytest.raises(ValueError, match="cannot be None"):
            mapper.to_list_dto(None)  # type: ignore
