"""Tests for task-related exceptions.

**Feature: realistic-test-coverage**
**Validates: Requirements 4.2**
"""

from core.errors.shared.task_errors import (
    BanOperationError,
    LockAcquisitionTimeoutError,
    RollbackError,
    TaskExecutionError,
)


class TestTaskExecutionError:
    """Tests for TaskExecutionError."""

    def test_init_with_message(self) -> None:
        """Test initialization with task_id and message."""
        error = TaskExecutionError("task-123", "Processing failed")
        assert error.task_id == "task-123"
        assert error.cause is None
        assert "task-123" in str(error)
        assert "Processing failed" in str(error)

    def test_init_with_cause(self) -> None:
        """Test initialization with cause exception."""
        cause = ValueError("Invalid input")
        error = TaskExecutionError("task-456", "Validation error", cause=cause)
        assert error.task_id == "task-456"
        assert error.cause is cause
        assert "task-456" in str(error)

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""
        error = TaskExecutionError("task-789", "Test error")
        assert isinstance(error, Exception)

    def test_message_format(self) -> None:
        """Test error message format."""
        error = TaskExecutionError("my-task", "Something went wrong")
        assert str(error) == "Task my-task: Something went wrong"


class TestBanOperationError:
    """Tests for BanOperationError."""

    def test_init_with_message(self) -> None:
        """Test initialization with message."""
        error = BanOperationError("Ban check failed")
        assert "Ban check failed" in str(error)

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""
        error = BanOperationError("Test error")
        assert isinstance(error, Exception)


class TestLockAcquisitionTimeoutError:
    """Tests for LockAcquisitionTimeoutError."""

    def test_init_with_identifier_and_timeout(self) -> None:
        """Test initialization with identifier and timeout."""
        error = LockAcquisitionTimeoutError("resource-123", 30.0)
        assert error.identifier == "resource-123"
        assert error.timeout == 30.0
        assert "resource-123" in str(error)
        assert "30" in str(error)

    def test_message_format(self) -> None:
        """Test error message format."""
        error = LockAcquisitionTimeoutError("my-lock", 5.5)
        assert str(error) == "Lock for 'my-lock' not acquired within 5.5s"

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""
        error = LockAcquisitionTimeoutError("test", 1.0)
        assert isinstance(error, Exception)

    def test_with_zero_timeout(self) -> None:
        """Test with zero timeout."""
        error = LockAcquisitionTimeoutError("instant", 0.0)
        assert error.timeout == 0.0
        assert "0.0s" in str(error)


class TestRollbackError:
    """Tests for RollbackError."""

    def test_init_with_errors(self) -> None:
        """Test initialization with original and rollback errors."""
        original = ValueError("Original failure")
        rollback = RuntimeError("Rollback failure")
        error = RollbackError(original, rollback)
        assert error.original_error is original
        assert error.rollback_error is rollback

    def test_message_contains_both_errors(self) -> None:
        """Test that message contains both error descriptions."""
        original = ValueError("Data corruption")
        rollback = OSError("Disk full")
        error = RollbackError(original, rollback)
        message = str(error)
        assert "Rollback failed" in message
        assert "Disk full" in message
        assert "Data corruption" in message

    def test_inherits_from_exception(self) -> None:
        """Test that error inherits from Exception."""
        error = RollbackError(Exception("a"), Exception("b"))
        assert isinstance(error, Exception)

    def test_with_nested_exceptions(self) -> None:
        """Test with nested exception chains."""
        inner = ValueError("Inner error")
        original = RuntimeError("Outer error")
        original.__cause__ = inner
        rollback = OSError("Rollback error")
        error = RollbackError(original, rollback)
        assert error.original_error is original
        assert error.rollback_error is rollback
