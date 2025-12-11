"""Unit tests for batch operation types.

Tests BatchOperationType, BatchErrorStrategy, BatchResult, BatchConfig,
BatchProgress, and BatchOperationStats.
"""

import pytest

from application.common.batch.config.config import (
    BatchConfig,
    BatchErrorStrategy,
    BatchOperationStats,
    BatchOperationType,
    BatchProgress,
    BatchResult,
)


class TestBatchOperationType:
    """Tests for BatchOperationType enum."""

    def test_create_value(self) -> None:
        """Test CREATE value."""
        assert BatchOperationType.CREATE.value == "create"

    def test_update_value(self) -> None:
        """Test UPDATE value."""
        assert BatchOperationType.UPDATE.value == "update"

    def test_delete_value(self) -> None:
        """Test DELETE value."""
        assert BatchOperationType.DELETE.value == "delete"

    def test_upsert_value(self) -> None:
        """Test UPSERT value."""
        assert BatchOperationType.UPSERT.value == "upsert"


class TestBatchErrorStrategy:
    """Tests for BatchErrorStrategy enum."""

    def test_fail_fast_value(self) -> None:
        """Test FAIL_FAST value."""
        assert BatchErrorStrategy.FAIL_FAST.value == "fail_fast"

    def test_continue_value(self) -> None:
        """Test CONTINUE value."""
        assert BatchErrorStrategy.CONTINUE.value == "continue"

    def test_rollback_value(self) -> None:
        """Test ROLLBACK value."""
        assert BatchErrorStrategy.ROLLBACK.value == "rollback"


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_creation(self) -> None:
        """Test BatchResult creation."""
        result = BatchResult[str](
            succeeded=["a", "b", "c"],
            failed=[],
            total_processed=3,
            total_succeeded=3,
            total_failed=0,
        )

        assert len(result.succeeded) == 3
        assert len(result.failed) == 0
        assert result.total_processed == 3

    def test_success_rate_all_success(self) -> None:
        """Test success rate with all successes."""
        result = BatchResult[str](
            succeeded=["a", "b"],
            failed=[],
            total_processed=2,
            total_succeeded=2,
            total_failed=0,
        )

        assert result.success_rate == 100.0

    def test_success_rate_partial(self) -> None:
        """Test success rate with partial success."""
        result = BatchResult[str](
            succeeded=["a"],
            failed=[("b", ValueError("error"))],
            total_processed=2,
            total_succeeded=1,
            total_failed=1,
        )

        assert result.success_rate == 50.0

    def test_success_rate_empty(self) -> None:
        """Test success rate with no items."""
        result = BatchResult[str](
            succeeded=[],
            failed=[],
            total_processed=0,
            total_succeeded=0,
            total_failed=0,
        )

        assert result.success_rate == 100.0

    def test_is_complete_success(self) -> None:
        """Test is_complete_success property."""
        result = BatchResult[str](
            succeeded=["a", "b"],
            failed=[],
            total_processed=2,
            total_succeeded=2,
            total_failed=0,
        )

        assert result.is_complete_success is True

    def test_is_complete_success_with_failures(self) -> None:
        """Test is_complete_success with failures."""
        result = BatchResult[str](
            succeeded=["a"],
            failed=[("b", ValueError("error"))],
            total_processed=2,
            total_succeeded=1,
            total_failed=1,
        )

        assert result.is_complete_success is False

    def test_has_failures(self) -> None:
        """Test has_failures property."""
        result = BatchResult[str](
            succeeded=["a"],
            failed=[("b", ValueError("error"))],
            total_processed=2,
            total_succeeded=1,
            total_failed=1,
        )

        assert result.has_failures is True

    def test_has_failures_rolled_back(self) -> None:
        """Test has_failures when rolled back."""
        result = BatchResult[str](
            succeeded=[],
            failed=[],
            total_processed=2,
            total_succeeded=0,
            total_failed=0,
            rolled_back=True,
        )

        assert result.has_failures is True


class TestBatchConfig:
    """Tests for BatchConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BatchConfig()

        assert config.chunk_size == 100
        assert config.max_concurrent == 5
        assert config.error_strategy == BatchErrorStrategy.CONTINUE
        assert config.retry_failed is False
        assert config.max_retries == 3
        assert config.timeout_per_chunk is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BatchConfig(
            chunk_size=50,
            max_concurrent=10,
            error_strategy=BatchErrorStrategy.FAIL_FAST,
            retry_failed=True,
            max_retries=5,
            timeout_per_chunk=30.0,
        )

        assert config.chunk_size == 50
        assert config.max_concurrent == 10
        assert config.error_strategy == BatchErrorStrategy.FAIL_FAST
        assert config.retry_failed is True
        assert config.max_retries == 5
        assert config.timeout_per_chunk == 30.0

    def test_invalid_chunk_size(self) -> None:
        """Test validation of chunk_size."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            BatchConfig(chunk_size=0)

    def test_invalid_max_concurrent(self) -> None:
        """Test validation of max_concurrent."""
        with pytest.raises(ValueError, match="max_concurrent must be positive"):
            BatchConfig(max_concurrent=-1)

    def test_invalid_max_retries(self) -> None:
        """Test validation of max_retries."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            BatchConfig(max_retries=-1)

    def test_invalid_timeout(self) -> None:
        """Test validation of timeout_per_chunk."""
        with pytest.raises(ValueError, match="timeout_per_chunk must be positive"):
            BatchConfig(timeout_per_chunk=0)


class TestBatchProgress:
    """Tests for BatchProgress dataclass."""

    def test_creation(self) -> None:
        """Test BatchProgress creation."""
        progress = BatchProgress(total_items=100)

        assert progress.total_items == 100
        assert progress.processed_items == 0
        assert progress.succeeded_items == 0
        assert progress.failed_items == 0
        assert progress.current_chunk == 0
        assert progress.total_chunks == 0

    def test_progress_percentage(self) -> None:
        """Test progress percentage calculation."""
        progress = BatchProgress(
            total_items=100,
            processed_items=50,
        )

        assert progress.progress_percentage == 50.0

    def test_progress_percentage_empty(self) -> None:
        """Test progress percentage with no items."""
        progress = BatchProgress(total_items=0)

        assert progress.progress_percentage == 100.0

    def test_is_complete(self) -> None:
        """Test is_complete property."""
        progress = BatchProgress(
            total_items=100,
            processed_items=100,
        )

        assert progress.is_complete is True

    def test_is_complete_false(self) -> None:
        """Test is_complete when not complete."""
        progress = BatchProgress(
            total_items=100,
            processed_items=50,
        )

        assert progress.is_complete is False


class TestBatchOperationStats:
    """Tests for BatchOperationStats dataclass."""

    def test_creation(self) -> None:
        """Test BatchOperationStats creation."""
        stats = BatchOperationStats(
            operation_type=BatchOperationType.CREATE,
            total_items=100,
            succeeded=95,
            failed=5,
        )

        assert stats.operation_type == BatchOperationType.CREATE
        assert stats.total_items == 100
        assert stats.succeeded == 95
        assert stats.failed == 5

    def test_success_rate(self) -> None:
        """Test success rate calculation."""
        stats = BatchOperationStats(
            operation_type=BatchOperationType.UPDATE,
            total_items=100,
            succeeded=80,
            failed=20,
        )

        assert stats.success_rate == 80.0

    def test_success_rate_empty(self) -> None:
        """Test success rate with no items."""
        stats = BatchOperationStats(
            operation_type=BatchOperationType.DELETE,
            total_items=0,
        )

        assert stats.success_rate == 100.0
