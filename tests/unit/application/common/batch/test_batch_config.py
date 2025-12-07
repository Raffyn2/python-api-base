"""Unit tests for batch configuration and result types.

Tests BatchConfig, BatchResult, BatchProgress, and BatchOperationStats.
"""

import pytest

from application.common.batch import (
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
        """Test CREATE operation type value."""
        assert BatchOperationType.CREATE.value == "create"

    def test_update_value(self) -> None:
        """Test UPDATE operation type value."""
        assert BatchOperationType.UPDATE.value == "update"

    def test_delete_value(self) -> None:
        """Test DELETE operation type value."""
        assert BatchOperationType.DELETE.value == "delete"

    def test_upsert_value(self) -> None:
        """Test UPSERT operation type value."""
        assert BatchOperationType.UPSERT.value == "upsert"


class TestBatchErrorStrategy:
    """Tests for BatchErrorStrategy enum."""

    def test_fail_fast_value(self) -> None:
        """Test FAIL_FAST strategy value."""
        assert BatchErrorStrategy.FAIL_FAST.value == "fail_fast"

    def test_continue_value(self) -> None:
        """Test CONTINUE strategy value."""
        assert BatchErrorStrategy.CONTINUE.value == "continue"

    def test_rollback_value(self) -> None:
        """Test ROLLBACK strategy value."""
        assert BatchErrorStrategy.ROLLBACK.value == "rollback"


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

    def test_invalid_chunk_size_raises(self) -> None:
        """Test invalid chunk_size raises ValueError."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            BatchConfig(chunk_size=0)

    def test_negative_chunk_size_raises(self) -> None:
        """Test negative chunk_size raises ValueError."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            BatchConfig(chunk_size=-1)

    def test_invalid_max_concurrent_raises(self) -> None:
        """Test invalid max_concurrent raises ValueError."""
        with pytest.raises(ValueError, match="max_concurrent must be positive"):
            BatchConfig(max_concurrent=0)

    def test_negative_max_retries_raises(self) -> None:
        """Test negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            BatchConfig(max_retries=-1)

    def test_invalid_timeout_raises(self) -> None:
        """Test invalid timeout_per_chunk raises ValueError."""
        with pytest.raises(ValueError, match="timeout_per_chunk must be positive"):
            BatchConfig(timeout_per_chunk=0)

    def test_negative_timeout_raises(self) -> None:
        """Test negative timeout_per_chunk raises ValueError."""
        with pytest.raises(ValueError, match="timeout_per_chunk must be positive"):
            BatchConfig(timeout_per_chunk=-1.0)


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_complete_success(self) -> None:
        """Test BatchResult with all successes."""
        result = BatchResult(
            succeeded=["a", "b", "c"],
            failed=[],
            total_processed=3,
            total_succeeded=3,
            total_failed=0,
        )
        assert result.is_complete_success is True
        assert result.has_failures is False
        assert result.success_rate == 100.0

    def test_partial_success(self) -> None:
        """Test BatchResult with partial success."""
        result = BatchResult(
            succeeded=["a", "b"],
            failed=[("c", ValueError("error"))],
            total_processed=3,
            total_succeeded=2,
            total_failed=1,
        )
        assert result.is_complete_success is False
        assert result.has_failures is True
        assert result.success_rate == pytest.approx(66.67, rel=0.01)

    def test_complete_failure(self) -> None:
        """Test BatchResult with all failures."""
        result = BatchResult(
            succeeded=[],
            failed=[("a", ValueError("e1")), ("b", ValueError("e2"))],
            total_processed=2,
            total_succeeded=0,
            total_failed=2,
        )
        assert result.is_complete_success is False
        assert result.has_failures is True
        assert result.success_rate == 0.0

    def test_empty_batch(self) -> None:
        """Test BatchResult with empty batch."""
        result = BatchResult(
            succeeded=[],
            failed=[],
            total_processed=0,
            total_succeeded=0,
            total_failed=0,
        )
        assert result.is_complete_success is True
        assert result.has_failures is False
        assert result.success_rate == 100.0

    def test_rolled_back(self) -> None:
        """Test BatchResult with rollback."""
        result = BatchResult(
            succeeded=[],
            failed=[],
            total_processed=3,
            total_succeeded=0,
            total_failed=0,
            rolled_back=True,
            rollback_error=ValueError("rollback failed"),
        )
        assert result.is_complete_success is False
        assert result.has_failures is True

    def test_frozen_dataclass(self) -> None:
        """Test BatchResult is immutable."""
        result = BatchResult(
            succeeded=["a"],
            failed=[],
            total_processed=1,
            total_succeeded=1,
            total_failed=0,
        )
        with pytest.raises(AttributeError):
            result.total_processed = 10  # type: ignore[misc]


class TestBatchProgress:
    """Tests for BatchProgress dataclass."""

    def test_initial_progress(self) -> None:
        """Test initial progress state."""
        progress = BatchProgress(total_items=100)
        assert progress.processed_items == 0
        assert progress.succeeded_items == 0
        assert progress.failed_items == 0
        assert progress.progress_percentage == 0.0
        assert progress.is_complete is False

    def test_partial_progress(self) -> None:
        """Test partial progress."""
        progress = BatchProgress(
            total_items=100,
            processed_items=50,
            succeeded_items=45,
            failed_items=5,
        )
        assert progress.progress_percentage == 50.0
        assert progress.is_complete is False

    def test_complete_progress(self) -> None:
        """Test complete progress."""
        progress = BatchProgress(
            total_items=100,
            processed_items=100,
            succeeded_items=95,
            failed_items=5,
        )
        assert progress.progress_percentage == 100.0
        assert progress.is_complete is True

    def test_empty_batch_progress(self) -> None:
        """Test progress with empty batch."""
        progress = BatchProgress(total_items=0)
        assert progress.progress_percentage == 100.0
        assert progress.is_complete is True

    def test_chunk_tracking(self) -> None:
        """Test chunk tracking."""
        progress = BatchProgress(
            total_items=100,
            current_chunk=2,
            total_chunks=5,
        )
        assert progress.current_chunk == 2
        assert progress.total_chunks == 5


class TestBatchOperationStats:
    """Tests for BatchOperationStats dataclass."""

    def test_create_stats(self) -> None:
        """Test stats for create operation."""
        stats = BatchOperationStats(
            operation_type=BatchOperationType.CREATE,
            total_items=100,
            succeeded=95,
            failed=5,
            duration_ms=1500.0,
            items_per_second=66.67,
            chunks_processed=10,
        )
        assert stats.operation_type == BatchOperationType.CREATE
        assert stats.success_rate == 95.0

    def test_empty_stats(self) -> None:
        """Test stats with no items."""
        stats = BatchOperationStats(operation_type=BatchOperationType.DELETE)
        assert stats.total_items == 0
        assert stats.success_rate == 100.0

    def test_all_failed_stats(self) -> None:
        """Test stats with all failures."""
        stats = BatchOperationStats(
            operation_type=BatchOperationType.UPDATE,
            total_items=10,
            succeeded=0,
            failed=10,
        )
        assert stats.success_rate == 0.0
