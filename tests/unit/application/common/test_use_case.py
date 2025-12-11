"""Unit tests for BaseUseCase class.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 2.1**
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.common.errors import NotFoundError, ValidationError
from application.common.use_cases.base.use_case import BaseUseCase
from core.base.patterns.result import Err


@dataclass
class TestEntity:
    """Test entity for use case tests."""

    id: str
    name: str
    value: int


class TestUseCase(BaseUseCase[TestEntity, str]):
    """Concrete implementation for testing."""

    def __init__(self, repo: Any, uow: Any) -> None:
        self._repo = repo
        self._uow = uow

    async def _get_repository(self) -> Any:
        return self._repo

    async def _get_unit_of_work(self) -> Any:
        return self._uow

    def _get_entity_name(self) -> str:
        return "TestEntity"


@pytest.fixture()
def mock_repo() -> AsyncMock:
    """Create mock repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture()
def mock_uow() -> MagicMock:
    """Create mock unit of work."""
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture()
def use_case(mock_repo: AsyncMock, mock_uow: MagicMock) -> TestUseCase:
    """Create test use case."""
    return TestUseCase(mock_repo, mock_uow)


@pytest.fixture()
def sample_entity() -> TestEntity:
    """Create sample entity."""
    return TestEntity(id="1", name="Test", value=100)


class TestBaseUseCaseGet:
    """Tests for get method."""

    async def test_get_existing_entity(
        self, use_case: TestUseCase, mock_repo: AsyncMock, sample_entity: TestEntity
    ) -> None:
        """Test getting an existing entity."""
        mock_repo.get_by_id.return_value = sample_entity

        result = await use_case.get("1")

        assert result == sample_entity
        mock_repo.get_by_id.assert_called_once_with("1")

    async def test_get_missing_entity_raises(self, use_case: TestUseCase, mock_repo: AsyncMock) -> None:
        """Test getting missing entity raises NotFoundError."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await use_case.get("999", raise_on_missing=True)

    async def test_get_missing_entity_returns_none(self, use_case: TestUseCase, mock_repo: AsyncMock) -> None:
        """Test getting missing entity returns None when not raising."""
        mock_repo.get_by_id.return_value = None

        result = await use_case.get("999", raise_on_missing=False)

        assert result is None


class TestBaseUseCaseGetResult:
    """Tests for get_result method."""

    async def test_get_result_success(
        self, use_case: TestUseCase, mock_repo: AsyncMock, sample_entity: TestEntity
    ) -> None:
        """Test get_result returns Ok on success."""
        mock_repo.get_by_id.return_value = sample_entity

        result = await use_case.get_result("1")

        assert result.is_ok()
        assert result.unwrap() == sample_entity

    async def test_get_result_not_found(self, use_case: TestUseCase, mock_repo: AsyncMock) -> None:
        """Test get_result returns Err on not found."""
        mock_repo.get_by_id.return_value = None

        result = await use_case.get_result("999")

        assert result.is_err()


class TestBaseUseCaseList:
    """Tests for list method."""

    async def test_list_entities(self, use_case: TestUseCase, mock_repo: AsyncMock) -> None:
        """Test listing entities with pagination."""
        entities = [
            TestEntity(id="1", name="Test1", value=100),
            TestEntity(id="2", name="Test2", value=200),
        ]
        mock_repo.get_all.return_value = (entities, 2)

        result = await use_case.list(page=1, size=10)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.size == 10

    async def test_list_with_filters(self, use_case: TestUseCase, mock_repo: AsyncMock) -> None:
        """Test listing with filters."""
        mock_repo.get_all.return_value = ([], 0)

        await use_case.list(filters={"name": "Test"}, sort_by="name", sort_order="desc")

        mock_repo.get_all.assert_called_once()
        call_kwargs = mock_repo.get_all.call_args.kwargs
        assert call_kwargs["filters"] == {"name": "Test"}
        assert call_kwargs["sort_by"] == "name"
        assert call_kwargs["sort_order"] == "desc"


class TestBaseUseCaseCreate:
    """Tests for create method."""

    async def test_create_success(
        self, use_case: TestUseCase, mock_repo: AsyncMock, mock_uow: MagicMock, sample_entity: TestEntity
    ) -> None:
        """Test successful entity creation."""
        mock_repo.create.return_value = sample_entity

        result = await use_case.create({"name": "Test", "value": 100})

        assert result.is_ok()
        assert result.unwrap() == sample_entity
        mock_uow.commit.assert_called_once()

    async def test_create_validation_error(self, use_case: TestUseCase, mock_repo: AsyncMock) -> None:
        """Test create with validation error."""

        # Override validation to return error
        async def failing_validation(data: Any) -> Any:
            return Err(ValidationError("Invalid data"))

        use_case._validate_create = failing_validation

        result = await use_case.create({"invalid": "data"})

        assert result.is_err()


class TestBaseUseCaseUpdate:
    """Tests for update method."""

    async def test_update_success(
        self, use_case: TestUseCase, mock_repo: AsyncMock, mock_uow: MagicMock, sample_entity: TestEntity
    ) -> None:
        """Test successful entity update."""
        mock_repo.update.return_value = sample_entity

        result = await use_case.update("1", {"name": "Updated"})

        assert result.is_ok()
        mock_uow.commit.assert_called_once()

    async def test_update_not_found(self, use_case: TestUseCase, mock_repo: AsyncMock, mock_uow: MagicMock) -> None:
        """Test update returns error when entity not found."""
        mock_repo.update.return_value = None

        result = await use_case.update("999", {"name": "Updated"})

        assert result.is_err()


class TestBaseUseCaseDelete:
    """Tests for delete method."""

    async def test_delete_success(self, use_case: TestUseCase, mock_repo: AsyncMock, mock_uow: MagicMock) -> None:
        """Test successful entity deletion."""
        mock_repo.delete.return_value = True

        result = await use_case.delete("1")

        assert result.is_ok()
        assert result.unwrap() is True
        mock_uow.commit.assert_called_once()

    async def test_delete_not_found(self, use_case: TestUseCase, mock_repo: AsyncMock, mock_uow: MagicMock) -> None:
        """Test delete returns error when entity not found."""
        mock_repo.delete.return_value = False

        result = await use_case.delete("999")

        assert result.is_err()
