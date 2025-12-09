"""Unit tests for batch operation builder.

**Feature: test-coverage-90-percent**
**Validates: Requirements 1.2**
"""

from collections.abc import Sequence
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from application.common.batch.builders.builder import BatchOperationBuilder
from application.common.batch.config.config import (
    BatchConfig,
    BatchErrorStrategy,
    BatchProgress,
    BatchResult,
)


class TestItem(BaseModel):
    """Test item model."""
    id: str
    name: str


class CreateTestItem(BaseModel):
    """Test create item model."""
    name: str


class UpdateTestItem(BaseModel):
    """Test update item model."""
    name: str


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create mock batch repository."""
    repo = MagicMock()
    repo.bulk_create = AsyncMock(return_value=BatchResult(
        succeeded=[TestItem(id="1", name="test")],
        failed=[],
        total_processed=1,
        total_succeeded=1,
        total_failed=0
    ))
    repo.bulk_update = AsyncMock(return_value=BatchResult(
        succeeded=[TestItem(id="1", name="updated")],
        failed=[],
        total_processed=1,
        total_succeeded=1,
        total_failed=0
    ))
    repo.bulk_delete = AsyncMock(return_value=BatchResult(
        succeeded=["1"],
        failed=[],
        total_processed=1,
        total_succeeded=1,
        total_failed=0
    ))
    repo.bulk_upsert = AsyncMock(return_value=BatchResult(
        succeeded=[TestItem(id="1", name="upserted")],
        failed=[],
        total_processed=1,
        total_succeeded=1,
        total_failed=0
    ))
    return repo


class TestBatchOperationBuilder:
    """Tests for BatchOperationBuilder class."""

    def test_init_with_repository(self, mock_repository: MagicMock) -> None:
        """Builder should initialize with repository."""
        builder = BatchOperationBuilder(mock_repository)
        
        assert builder._repository == mock_repository
        assert isinstance(builder._config, BatchConfig)

    def test_with_chunk_size(self, mock_repository: MagicMock) -> None:
        """with_chunk_size should set chunk size and return self."""
        builder = BatchOperationBuilder(mock_repository)
        
        result = builder.with_chunk_size(50)
        
        assert result is builder
        assert builder._config.chunk_size == 50

    def test_with_error_strategy(self, mock_repository: MagicMock) -> None:
        """with_error_strategy should set strategy and return self."""
        builder = BatchOperationBuilder(mock_repository)
        
        result = builder.with_error_strategy(BatchErrorStrategy.FAIL_FAST)
        
        assert result is builder
        assert builder._config.error_strategy == BatchErrorStrategy.FAIL_FAST

    def test_with_retry(self, mock_repository: MagicMock) -> None:
        """with_retry should enable retry and set max retries."""
        builder = BatchOperationBuilder(mock_repository)
        
        result = builder.with_retry(max_retries=5)
        
        assert result is builder
        assert builder._config.retry_failed is True
        assert builder._config.max_retries == 5

    def test_with_retry_default_retries(self, mock_repository: MagicMock) -> None:
        """with_retry should use default max retries."""
        builder = BatchOperationBuilder(mock_repository)
        
        builder.with_retry()
        
        assert builder._config.max_retries == 3

    def test_with_progress(self, mock_repository: MagicMock) -> None:
        """with_progress should set callback and return self."""
        builder = BatchOperationBuilder(mock_repository)
        callback = MagicMock()
        
        result = builder.with_progress(callback)
        
        assert result is builder
        assert builder._progress_callback == callback

    def test_fluent_chaining(self, mock_repository: MagicMock) -> None:
        """Builder methods should support fluent chaining."""
        builder = BatchOperationBuilder(mock_repository)
        callback = MagicMock()
        
        result = (
            builder
            .with_chunk_size(25)
            .with_error_strategy(BatchErrorStrategy.ROLLBACK)
            .with_retry(max_retries=2)
            .with_progress(callback)
        )
        
        assert result is builder
        assert builder._config.chunk_size == 25
        assert builder._config.error_strategy == BatchErrorStrategy.ROLLBACK
        assert builder._config.retry_failed is True
        assert builder._config.max_retries == 2
        assert builder._progress_callback == callback

    @pytest.mark.asyncio
    async def test_create(self, mock_repository: MagicMock) -> None:
        """create should call repository bulk_create."""
        builder = BatchOperationBuilder(mock_repository)
        items = [CreateTestItem(name="test")]
        
        result = await builder.create(items)
        
        mock_repository.bulk_create.assert_called_once()
        assert result.total_succeeded == 1

    @pytest.mark.asyncio
    async def test_create_with_config(self, mock_repository: MagicMock) -> None:
        """create should pass config to repository."""
        builder = BatchOperationBuilder(mock_repository)
        builder.with_chunk_size(10)
        items = [CreateTestItem(name="test")]
        
        await builder.create(items)
        
        call_kwargs = mock_repository.bulk_create.call_args.kwargs
        assert call_kwargs["config"].chunk_size == 10

    @pytest.mark.asyncio
    async def test_update(self, mock_repository: MagicMock) -> None:
        """update should call repository bulk_update."""
        builder = BatchOperationBuilder(mock_repository)
        items = [("1", UpdateTestItem(name="updated"))]
        
        result = await builder.update(items)
        
        mock_repository.bulk_update.assert_called_once()
        assert result.total_succeeded == 1

    @pytest.mark.asyncio
    async def test_delete(self, mock_repository: MagicMock) -> None:
        """delete should call repository bulk_delete."""
        builder = BatchOperationBuilder(mock_repository)
        ids = ["1", "2", "3"]
        
        result = await builder.delete(ids)
        
        mock_repository.bulk_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_soft(self, mock_repository: MagicMock) -> None:
        """delete should pass soft parameter."""
        builder = BatchOperationBuilder(mock_repository)
        
        await builder.delete(["1"], soft=True)
        
        call_kwargs = mock_repository.bulk_delete.call_args.kwargs
        assert call_kwargs["soft"] is True

    @pytest.mark.asyncio
    async def test_delete_hard(self, mock_repository: MagicMock) -> None:
        """delete should support hard delete."""
        builder = BatchOperationBuilder(mock_repository)
        
        await builder.delete(["1"], soft=False)
        
        call_kwargs = mock_repository.bulk_delete.call_args.kwargs
        assert call_kwargs["soft"] is False

    @pytest.mark.asyncio
    async def test_upsert(self, mock_repository: MagicMock) -> None:
        """upsert should call repository bulk_upsert."""
        builder = BatchOperationBuilder(mock_repository)
        items = [CreateTestItem(name="test")]
        
        result = await builder.upsert(items)
        
        mock_repository.bulk_upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_with_key_field(self, mock_repository: MagicMock) -> None:
        """upsert should pass key_field parameter."""
        builder = BatchOperationBuilder(mock_repository)
        items = [CreateTestItem(name="test")]
        
        await builder.upsert(items, key_field="name")
        
        call_kwargs = mock_repository.bulk_upsert.call_args.kwargs
        assert call_kwargs["key_field"] == "name"

    @pytest.mark.asyncio
    async def test_progress_callback_passed(self, mock_repository: MagicMock) -> None:
        """Progress callback should be passed to repository."""
        builder = BatchOperationBuilder(mock_repository)
        callback = MagicMock()
        builder.with_progress(callback)
        
        await builder.create([CreateTestItem(name="test")])
        
        call_kwargs = mock_repository.bulk_create.call_args.kwargs
        assert call_kwargs["on_progress"] == callback
