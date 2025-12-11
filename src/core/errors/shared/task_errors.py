"""Task-related exceptions.

**Feature: shared-modules-refactoring**
**Refactored: Split from exceptions.py for one-class-per-file compliance**
"""

from __future__ import annotations

from core.errors.shared.base import SharedModuleError


class TaskExecutionError(SharedModuleError):
    """Error during background task execution.

    Attributes:
        task_id: Identifier of the failed task.
        cause: Original exception that caused the failure.
    """

    def __init__(
        self,
        task_id: str,
        message: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize task execution error.

        Args:
            task_id: Identifier of the failed task.
            message: Human-readable error message.
            cause: Original exception that caused the failure.
        """
        self.task_id = task_id
        self.cause = cause
        super().__init__(f"Task {task_id}: {message}")


class BanOperationError(SharedModuleError):
    """Error during ban operations in auto-ban system.

    Raised when ban check, record, or lift operations fail.
    """


class LockAcquisitionTimeoutError(SharedModuleError):
    """Lock acquisition timed out.

    Raised when a lock cannot be acquired within the specified timeout.

    Attributes:
        identifier: The identifier for which lock acquisition failed.
        timeout: The timeout duration in seconds.
    """

    def __init__(self, identifier: str, timeout: float) -> None:
        """Initialize lock acquisition timeout error.

        Args:
            identifier: The identifier for which lock acquisition failed.
            timeout: The timeout duration in seconds.
        """
        self.identifier = identifier
        self.timeout = timeout
        super().__init__(f"Lock for '{identifier}' not acquired within {timeout}s")


class RollbackError(SharedModuleError):
    """Error during rollback operation in batch processing.

    Raised when a rollback operation fails, containing both the original
    error that triggered the rollback and the error that occurred during rollback.

    Attributes:
        original_error: The exception that triggered the rollback.
        rollback_error: The exception that occurred during rollback.
    """

    def __init__(
        self,
        original_error: Exception,
        rollback_error: Exception,
    ) -> None:
        """Initialize rollback error.

        Args:
            original_error: The exception that triggered the rollback.
            rollback_error: The exception that occurred during rollback.
        """
        self.original_error = original_error
        self.rollback_error = rollback_error
        super().__init__(f"Rollback failed: {rollback_error} (original error: {original_error})")
