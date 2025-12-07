"""Unit tests for BaseUseCase.

Tests CRUD operations and hooks.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.common.dto import PaginatedResponse
from application.common.errors import NotFoundError, ValidationError
from application.common.use_cases import BaseUseCase
from core.base.patterns.result import Err, Ok


@dataclass
class SampleEntity:
    """Sample entity for testing."""

    id: str
    name: str


class SampleUseCase(BaseUseCase[SampleEntity, str]):
    """Concrete use case for testing."""

    def __init__(self, repo: Any, uow: Any) -> None:
        self._repo = repo
        self._uow = uow

    async def _get_repository(self) -> Any:
        return self._repo

    async def _get_unit_of_work(self) -> Any:
        return self._uow

    def _get_entity_name(self) -> str:
        return "SampleEntity"


class TestBaseUseCaseGet:
    """Tests for get operations."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_uow(self) -> MagicMock:
        """Create mock unit of work."""
        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.commit = AsyncMock()
        return uow

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock, mock_uow: MagicMock) -> SampleUseCase:
        """Create use case instance."""
        return SampleUseCase(mock_repo, mock_uow)

    @pytest.mark.asyncio
    async def test_get_returns_entity(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test get returns entity when found."""
        entity = SampleEntity(id="1", name="Test")
        mock_repo.get_by_id = AsyncMock(return_value=entity)

        result = await use_case.get("1")

        assert result == entity
        mock_repo.get_by_id.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_get_raises_not_found(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test get raises NotFoundError when not found."""
        mock_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await use_case.get("1", raise_on_missing=True)

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_raising(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test get returns None when raise_on_missing=False."""
        mock_repo.get_by_id = AsyncMock(return_value=None)

        result = await use_case.get("1", raise_on_missing=False)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_result_returns_ok(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test get_result returns Ok when found."""
        entity = SampleEntity(id="1", name="Test")
        mock_repo.get_by_id = AsyncMock(return_value=entity)

        result = await use_case.get_result("1")

        assert result.is_ok()
        assert result.value == entity

    @pytest.mark.asyncio
    async def test_get_result_returns_err(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test get_result returns Err when not found."""
        mock_repo.get_by_id = AsyncMock(return_value=None)

        result = await use_case.get_result("1")

        assert result.is_err()


class TestBaseUseCaseList:
    """Tests for list operations."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_uow(self) -> MagicMock:
        """Create mock unit of work."""
        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.commit = AsyncMock()
        return uow

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock, mock_uow: MagicMock) -> SampleUseCase:
        """Create use case instance."""
        return SampleUseCase(mock_repo, mock_uow)

    @pytest.mark.asyncio
    async def test_list_returns_paginated_response(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test list returns PaginatedResponse."""
        entities = [SampleEntity(id="1", name="One"), SampleEntity(id="2", name="Two")]
        mock_repo.get_all = AsyncMock(return_value=(entities, 2))

        result = await use_case.list(page=1, size=10)

        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 2
        assert result.total == 2
        assert result.page == 1
        assert result.size == 10

    @pytest.mark.asyncio
    async def test_list_calculates_skip(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test list calculates skip correctly."""
        mock_repo.get_all = AsyncMock(return_value=([], 0))

        await use_case.list(page=3, size=10)

        mock_repo.get_all.assert_called_once()
        call_kwargs = mock_repo.get_all.call_args.kwargs
        assert call_kwargs["skip"] == 20
        assert call_kwargs["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_passes_filters(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test list passes filters to repository."""
        mock_repo.get_all = AsyncMock(return_value=([], 0))
        filters = {"status": "active"}

        await use_case.list(filters=filters)

        call_kwargs = mock_repo.get_all.call_args.kwargs
        assert call_kwargs["filters"] == filters


class TestBaseUseCaseCreate:
    """Tests for create operations."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_uow(self) -> MagicMock:
        """Create mock unit of work."""
        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.commit = AsyncMock()
        return uow

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock, mock_uow: MagicMock) -> SampleUseCase:
        """Create use case instance."""
        return SampleUseCase(mock_repo, mock_uow)

    @pytest.mark.asyncio
    async def test_create_returns_ok(
        self, use_case: SampleUseCase, mock_repo: AsyncMock, mock_uow: MagicMock
    ) -> None:
        """Test create returns Ok on success."""
        entity = SampleEntity(id="1", name="Test")
        mock_repo.create = AsyncMock(return_value=entity)

        result = await use_case.create({"name": "Test"})

        assert result.is_ok()
        assert result.value == entity
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_calls_after_hook(
        self, use_case: SampleUseCase, mock_repo: AsyncMock, mock_uow: MagicMock
    ) -> None:
        """Test create calls _after_create hook."""
        entity = SampleEntity(id="1", name="Test")
        mock_repo.create = AsyncMock(return_value=entity)
        use_case._after_create = AsyncMock()

        await use_case.create({"name": "Test"})

        use_case._after_create.assert_called_once_with(entity)


class TestBaseUseCaseUpdate:
    """Tests for update operations."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_uow(self) -> MagicMock:
        """Create mock unit of work."""
        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.commit = AsyncMock()
        return uow

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock, mock_uow: MagicMock) -> SampleUseCase:
        """Create use case instance."""
        return SampleUseCase(mock_repo, mock_uow)

    @pytest.mark.asyncio
    async def test_update_returns_ok(
        self, use_case: SampleUseCase, mock_repo: AsyncMock, mock_uow: MagicMock
    ) -> None:
        """Test update returns Ok on success."""
        entity = SampleEntity(id="1", name="Updated")
        mock_repo.update = AsyncMock(return_value=entity)

        result = await use_case.update("1", {"name": "Updated"})

        assert result.is_ok()
        assert result.value == entity

    @pytest.mark.asyncio
    async def test_update_returns_err_not_found(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test update returns Err when not found."""
        mock_repo.update = AsyncMock(return_value=None)

        result = await use_case.update("1", {"name": "Updated"})

        assert result.is_err()


class TestBaseUseCaseDelete:
    """Tests for delete operations."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_uow(self) -> MagicMock:
        """Create mock unit of work."""
        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.commit = AsyncMock()
        return uow

    @pytest.fixture
    def use_case(self, mock_repo: AsyncMock, mock_uow: MagicMock) -> SampleUseCase:
        """Create use case instance."""
        return SampleUseCase(mock_repo, mock_uow)

    @pytest.mark.asyncio
    async def test_delete_returns_ok(
        self, use_case: SampleUseCase, mock_repo: AsyncMock, mock_uow: MagicMock
    ) -> None:
        """Test delete returns Ok on success."""
        mock_repo.delete = AsyncMock(return_value=True)

        result = await use_case.delete("1")

        assert result.is_ok()
        assert result.value is True

    @pytest.mark.asyncio
    async def test_delete_returns_err_not_found(
        self, use_case: SampleUseCase, mock_repo: AsyncMock
    ) -> None:
        """Test delete returns Err when not found."""
        mock_repo.delete = AsyncMock(return_value=False)

        result = await use_case.delete("1")

        assert result.is_err()
