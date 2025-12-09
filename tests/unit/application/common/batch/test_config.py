"""Unit tests for batch configuration.

**Feature: test-coverage-90-percent**
**Validates: Requirements 1.2**
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

    def test_create_type(self) -> None:
        """CREATE should have correct value."""
        assert BatchOperationType.CREATE.value == "create"

    def test_update_type(self) -> None:
        """UPDATE should have correct value."""
        assert BatchOperationType.UPDATE.value == "update"

    def test_delete_type(self) -> None:
        """DELETE should have correct value."""
        assert BatchOperationType.DELETE.value == "delete"

    def test_upsert_type(self) -> None:
        """UPSERT should have correct value."""
        assert BatchOperationType.UPSERT.value == "upsert"


class TestBatchErrorStrategy:
    """Tests for BatchErrorStrategy enum."""

    def test_fail_fast_strategy(self) -> None:
        """FAIL_FAST should have correct value."""
        assert BatchErrorStrategy.FAIL_FAST.value == "fail_fast"

    def test_continue_strategy(self) -> None:
        """CONTINUE should have correct value."""
        assert BatchErrorStrategy.CONTINUE.value == "continue"

    def test_rollback_strategy(self) -> None:
        """ROLLBACK should have correct value."""
        assert BatchErrorStrategy.ROLLBACK.value == "rollback"


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_create_successful_result(self) -> None:
        """BatchResult should store successful items."""
        result = BatchResult(
            succeeded=["item1", "item2"],
            failed=[],
            total_processed=2,
            total_succeeded=2,
            total_failed=0
        )
        
        assert result.succeeded == ["item1", "item2"]
        assert result.total_succeeded == 2
        assert result.total_failed == 0

    def test_create_result_with_failures(self) -> None:
        """BatchResult should store failed items."""
        error = ValueError("test error")
        result = BatchResult(
            succeeded=["item1"],
        