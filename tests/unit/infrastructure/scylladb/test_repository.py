"""Unit tests for ScyllaDB repository.

**Feature: observability-infrastructure**
**Validates: R4 - Generic ScyllaDB Repository security and functionality**
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from infrastructure.scylladb.entity import ScyllaDBEntity
from infrastructure.scylladb.repository import (
    ScyllaDBRepository,
    _validate_identifier,
)


class UserEntity(ScyllaDBEntity):
    """Entity for repository tests."""

    __table_name__: ClassVar[str] = "users"
    __primary_key__: ClassVar[list[str]] = ["id"]

    name: str
    email: str


class TestValidateIdentifier:
    """Tests for CQL identifier validation - security critical."""

    def test_valid_identifier(self) -> None:
        """Valid identifiers should pass."""
        assert _validate_identifier("users", "table") == "users"
        assert _validate_identifier("user_name", "column") == "user_name"
        assert _validate_identifier("_private", "column") == "_private"
        assert _validate_identifier("Table123", "table") == "Table123"

    def test_invalid_identifier_empty(self) -> None:
        """Empty identifier should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid CQL"):
            _validate_identifier("", "table")

    def test_invalid_identifier_starts_with_number(self) -> None:
        """Identifier starting with number should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid CQL"):
            _validate_identifier("123table", "table")

    def test_invalid_identifier_special_chars(self) -> None:
        """Identifier with special chars should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid CQL"):
            _validate_identifier("user-name", "column")

    def test_sql_injection_attempt_semicolon(self) -> None:
        """SQL injection with semicolon should be rejected."""
        with pytest.raises(ValueError, match="Invalid CQL"):
            _validate_identifier("users; DROP TABLE users;--", "table")

    def test_sql_injection_attempt_quote(self) -> None:
        """SQL injection with quote should be rejected."""
        with pytest.raises(ValueError, match="Invalid CQL"):
            _validate_identifier("users' OR '1'='1", "table")


class TestScyllaDBRepository:
    """Tests for ScyllaDBRepository."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create mock ScyllaDB client."""
        client = MagicMock()
        client.execute = AsyncMock(return_value=[])
        client.prepare = AsyncMock(return_value=MagicMock())
        return client

    @pytest.fixture
    def repository(self, mock_client: MagicMock) -> ScyllaDBRepository[UserEntity]:
        """Create repository with mock client."""
        return ScyllaDBRepository[UserEntity](mock_client, UserEntity)

    def test_table_name_validation(self, repository: ScyllaDBRepository) -> None:
        """Table name should be validated."""
        assert repository.table_name == "users"

    def test_validate_columns(self, repository: ScyllaDBRepository) -> None:
        """Column names should be validated."""
        valid = repository._validate_columns(["id", "name", "email"])
        assert valid == ["id", "name", "email"]

    def test_validate_columns_rejects_invalid(
        self, repository: ScyllaDBRepository
    ) -> None:
        """Invalid column names should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid CQL"):
            repository._validate_columns(["id", "name; DROP TABLE", "email"])

    @pytest.mark.asyncio
    async def test_create_entity(
        self, repository: ScyllaDBRepository, mock_client: MagicMock
    ) -> None:
        """Create should insert entity with prepared statement."""
        user = UserEntity(name="John", email="john@example.com")

        result = await repository.create(user)

        assert result.name == "John"
        mock_client.prepare.assert_called()
        mock_client.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_entity_found(
        self, repository: ScyllaDBRepository, mock_client: MagicMock
    ) -> None:
        """Get should return entity when found."""
        user_id = uuid4()
        mock_row = MagicMock()
        mock_row._asdict.return_value = {
            "id": user_id,
            "name": "John",
            "email": "john@example.com",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        mock_client.execute = AsyncMock(return_value=[mock_row])

        result = await repository.get(user_id)

        assert result is not None
        assert result.name == "John"

    @pytest.mark.asyncio
    async def test_get_entity_not_found(
        self, repository: ScyllaDBRepository, mock_client: MagicMock
    ) -> None:
        """Get should return None when not found."""
        mock_client.execute = AsyncMock(return_value=[])

        result = await repository.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity(
        self, repository: ScyllaDBRepository, mock_client: MagicMock
    ) -> None:
        """Delete should execute delete statement."""
        await repository.delete(uuid4())

        mock_client.prepare.assert_called()
        mock_client.execute.assert_called()

    @pytest.mark.asyncio
    async def test_find_all_with_limit(
        self, repository: ScyllaDBRepository, mock_client: MagicMock
    ) -> None:
        """Find all should respect limit parameter."""
        mock_client.execute = AsyncMock(return_value=[])

        await repository.find_all(limit=50)

        mock_client.prepare.assert_called()
        call_args = mock_client.execute.call_args
        assert 50 in call_args[0][1]

    @pytest.mark.asyncio
    async def test_count_entities(
        self, repository: ScyllaDBRepository, mock_client: MagicMock
    ) -> None:
        """Count should return entity count."""
        mock_row = MagicMock()
        mock_row.count = 42
        mock_client.execute = AsyncMock(return_value=[mock_row])

        result = await repository.count()

        assert result == 42
