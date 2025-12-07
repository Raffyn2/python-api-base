"""Unit tests for BatchOperationBuilder.

Tests fluent builder API for batch operations.
"""

from collections.abc import Sequence
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from application.common.batch.builders.builder import BatchOperationBuilder
from application.common.batch.config.config import (
    BatchConfig,
    BatchErrorStrategy,
    BatchResult,
    ProgressCallback,
)
from application.common.batch.interfaces.interfaces import IBatchRepository


class SampleModel(BaseModel):
    """Sample model for testing."""

    id: str
    name: str


class CreateModel(BaseModel):
    """Create model for testing."""

    name: str


class UpdateModel(BaseModel):
    """Update model for testing."""

    name: str


class MockBatchRepository:
    """Mock batch repository for testing."""

    def __init__(self) -> None:
        self.bulk_create = AsyncMock(
            return_value=BatchResult[SampleModel](
                succeeded=[SampleModel(id="1", name="Test")],
                failed=[],
                total_processed=1,
                total_succeeded=1,
                total_failed=0,
            )
        )
        self.bulk_update = AsyncMock(
            return_value=BatchResult[SampleModel](
                succeeded=[SampleModel(id="1", name="Updated")],
                failed=[],
                total_processed=1,
                total_succeeded=1,
                total_failed=0,
            )
        )
        self.bulk_delete = AsyncMock(
            return_value=BatchResult[str](
                succeeded=["1"],
                failed=[],
                total_processed=1,
                total_succeeded=1,
                total_failed=0,
            )
        )
        self.bulk_upsert = AsyncMock(
            return_value=BatchResult[SampleModel](
                succeeded=[SampleModel(id="1", name="Upserted")],
                failed=[],
                total_processed=1,
                total_succeeded=1,
                total_failed=0,
            )
        )


class TestBatchOperationBuilderInit:
    """Tests for builder initialization."""

    def test_init_with_repository(self) -> None:
        """Test builder initialization with repository."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)

        assert builder._repository is repo
        assert builder._config is not None
        assert builder._progress_callback is None


class TestBatchOperationBuilderChaining:
    """Tests for fluent builder chaining."""

    def test_with_chunk_size(self) -> None:
        """Test with_chunk_size returns self for chaining."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)

        result = builder.with_chunk_size(50)

        assert result is builder
        assert builder._config.chunk_size == 50

    def test_with_error_strategy(self) -> None:
        """Test with_error_strategy returns self for chaining."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)

        result = builder.with_error_strategy(BatchErrorStrategy.FAIL_FAST)

        assert result is builder
        assert builder._config.error_strategy == BatchErrorStrategy.FAIL_FAST

    def test_with_retry(self) -> None:
        """Test with_retry returns self for chaining."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)

        result = builder.with_retry(max_retries=5)

        assert result is builder
        assert builder._config.retry_failed is True
        assert builder._config.max_retries == 5

    def test_with_retry_default(self) -> None:
        """Test with_retry with default max_retries."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)

        result = builder.with_retry()

        assert builder._config.retry_failed is True
        assert builder._config.max_retries == 3

    def test_with_progress(self) -> None:
        """Test with_progress returns self for chaining."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        callback = MagicMock()

        result = builder.with_progress(callback)

        assert result is builder
        assert builder._progress_callback is callback

    def test_chaining_multiple_methods(self) -> None:
        """Test chaining multiple builder methods."""
        repo = MockBatchRepository()
        callback = MagicMock()

        builder = (
            BatchOperationBuilder(repo)
            .with_chunk_size(25)
            .with_error_strategy(BatchErrorStrategy.ROLLBACK)
            .with_retry(max_retries=10)
            .with_progress(callback)
        )

        assert builder._config.chunk_size == 25
        assert builder._config.error_strategy == BatchErrorStrategy.ROLLBACK
        assert builder._config.retry_failed is True
        assert builder._config.max_retries == 10
        assert builder._progress_callback is callback


class TestBatchOperationBuilderCreate:
    """Tests for create operation."""

    @pytest.mark.asyncio
    async def test_create_calls_repository(self) -> None:
        """Test create calls repository bulk_create."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        items = [CreateModel(name="Test")]

        result = await builder.create(items)

        repo.bulk_create.assert_called_once()
        assert result.total_succeeded == 1

    @pytest.mark.asyncio
    async def test_create_passes_config(self) -> None:
        """Test create passes config to repository."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo).with_chunk_size(50)
        items = [CreateModel(name="Test")]

        await builder.create(items)

        call_args = repo.bulk_create.call_args
        assert call_args.kwargs["config"].chunk_size == 50

    @pytest.mark.asyncio
    async def test_create_passes_progress_callback(self) -> None:
        """Test create passes progress callback to repository."""
        repo = MockBatchRepository()
        callback = MagicMock()
        builder = BatchOperationBuilder(repo).with_progress(callback)
        items = [CreateModel(name="Test")]

        await builder.create(items)

        call_args = repo.bulk_create.call_args
        assert call_args.kwargs["on_progress"] is callback


class TestBatchOperationBuilderUpdate:
    """Tests for update operation."""

    @pytest.mark.asyncio
    async def test_update_calls_repository(self) -> None:
        """Test update calls repository bulk_update."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        items = [("1", UpdateModel(name="Updated"))]

        result = await builder.update(items)

        repo.bulk_update.assert_called_once()
        assert result.total_succeeded == 1

    @pytest.mark.asyncio
    async def test_update_passes_config(self) -> None:
        """Test update passes config to repository."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo).with_error_strategy(
            BatchErrorStrategy.FAIL_FAST
        )
        items = [("1", UpdateModel(name="Updated"))]

        await builder.update(items)

        call_args = repo.bulk_update.call_args
        assert call_args.kwargs["config"].error_strategy == BatchErrorStrategy.FAIL_FAST


class TestBatchOperationBuilderDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_calls_repository(self) -> None:
        """Test delete calls repository bulk_delete."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        ids = ["1", "2", "3"]

        result = await builder.delete(ids)

        repo.bulk_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_soft_default(self) -> None:
        """Test delete uses soft delete by default."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        ids = ["1"]

        await builder.delete(ids)

        call_args = repo.bulk_delete.call_args
        assert call_args.kwargs["soft"] is True

    @pytest.mark.asyncio
    async def test_delete_hard(self) -> None:
        """Test delete with hard delete."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        ids = ["1"]

        await builder.delete(ids, soft=False)

        call_args = repo.bulk_delete.call_args
        assert call_args.kwargs["soft"] is False


class TestBatchOperationBuilderUpsert:
    """Tests for upsert operation."""

    @pytest.mark.asyncio
    async def test_upsert_calls_repository(self) -> None:
        """Test upsert calls repository bulk_upsert."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        items = [CreateModel(name="Test")]

        result = await builder.upsert(items)

        repo.bulk_upsert.assert_called_once()
        assert result.total_succeeded == 1

    @pytest.mark.asyncio
    async def test_upsert_default_key_field(self) -> None:
        """Test upsert uses 'id' as default key field."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        items = [CreateModel(name="Test")]

        await builder.upsert(items)

        call_args = repo.bulk_upsert.call_args
        assert call_args.kwargs["key_field"] == "id"

    @pytest.mark.asyncio
    async def test_upsert_custom_key_field(self) -> None:
        """Test upsert with custom key field."""
        repo = MockBatchRepository()
        builder = BatchOperationBuilder(repo)
        items = [CreateModel(name="Test")]

        await builder.upsert(items, key_field="name")

        call_args = repo.bulk_upsert.call_args
        assert call_args.kwargs["key_field"] == "name"
