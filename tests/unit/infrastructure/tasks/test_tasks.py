"""Unit tests for tasks infrastructure.

**Feature: test-coverage-80-percent-v3**
"""

import pytest

from infrastructure.tasks.in_memory import InMemoryTaskQueue
from infrastructure.tasks.retry import ExponentialBackoff
from infrastructure.tasks.task import (
    Task,
    TaskPriority,
    TaskResult,
    TaskStatus,
)


class TestTask:
    """Tests for Task class."""

    def test_create_task(self) -> None:
        """Test creating a task."""
        task = Task[dict, str](
            name="test_task",
            payload={"key": "value"},
            handler="test.handler",
        )
        assert task.name == "test_task"
        assert task.payload == {"key": "value"}
        assert task.status == TaskStatus.PENDING
        assert task.task_id is not None

    def test_task_with_priority(self) -> None:
        """Test task with priority."""
        task = Task[dict, str](
            name="high_priority",
            payload={},
            handler="test.handler",
            priority=TaskPriority.HIGH,
        )
        assert task.priority == TaskPriority.HIGH

    def test_mark_running(self) -> None:
        """Test marking task as running."""
        task = Task[dict, str](
            name="test",
            payload={},
            handler="test.handler",
        )
        task.mark_running()

        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        assert task.attempt == 1

    def test_mark_completed(self) -> None:
        """Test marking task as completed."""
        task = Task[dict, str](
            name="test",
            payload={},
            handler="test.handler",
        )
        task.mark_completed("result", execution_time_ms=100.0)

        assert task.status == TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.success is True
        assert task.result.value == "result"

    def test_mark_failed(self) -> None:
        """Test marking task as failed."""
        task = Task[dict, str](
            name="test",
            payload={},
            handler="test.handler",
            max_attempts=3,
        )
        task.mark_failed("Error occurred")

        assert task.status == TaskStatus.RETRYING
        assert task.last_error == "Error occurred"

    def test_mark_failed_max_attempts(self) -> None:
        """Test marking task as failed after max attempts."""
        task = Task[dict, str](
            name="test",
            payload={},
            handler="test.handler",
            max_attempts=1,
        )
        task.attempt = 1
        task.mark_failed("Error occurred")

        assert task.status == TaskStatus.FAILED


class TestTaskResult:
    """Tests for TaskResult class."""

    def test_success_result(self) -> None:
        """Test successful result."""
        result = TaskResult[str](
            success=True,
            value="done",
            execution_time_ms=50.0,
        )
        assert result.success is True
        assert result.value == "done"

    def test_error_result(self) -> None:
        """Test error result."""
        result = TaskResult[str](
            success=False,
            error="Something went wrong",
            error_type="ValueError",
        )
        assert result.success is False
        assert result.error == "Something went wrong"


class TestInMemoryTaskQueue:
    """Tests for InMemoryTaskQueue."""

    @pytest.fixture()
    def queue(self) -> InMemoryTaskQueue:
        """Create in-memory queue."""
        return InMemoryTaskQueue()

    @pytest.mark.asyncio
    async def test_enqueue_task(self, queue: InMemoryTaskQueue) -> None:
        """Test enqueueing a task."""
        task = Task[dict, str](
            name="test",
            payload={},
            handler="test.handler",
        )
        await queue.enqueue(task)

        assert queue.total_count == 1

    @pytest.mark.asyncio
    async def test_dequeue_task(self, queue: InMemoryTaskQueue) -> None:
        """Test dequeueing a task."""
        task = Task[dict, str](
            name="test",
            payload={},
            handler="test.handler",
        )
        await queue.enqueue(task)

        dequeued = await queue.dequeue()

        assert dequeued is not None
        assert dequeued.name == "test"

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, queue: InMemoryTaskQueue) -> None:
        """Test dequeueing from empty queue."""
        result = await queue.dequeue()

        assert result is None


class TestExponentialBackoff:
    """Tests for ExponentialBackoff retry policy."""

    def test_default_backoff(self) -> None:
        """Test default backoff settings."""
        backoff = ExponentialBackoff()

        assert backoff.base_delay == 1.0
        assert backoff.max_delay == 300.0
        assert backoff.multiplier == 2.0

    def test_custom_backoff(self) -> None:
        """Test custom backoff settings."""
        backoff = ExponentialBackoff(
            base_delay=0.5,
            max_delay=30.0,
            multiplier=3.0,
        )

        assert backoff.base_delay == 0.5
        assert backoff.max_delay == 30.0
        assert backoff.multiplier == 3.0

    def test_calculate_delay(self) -> None:
        """Test delay calculation."""
        backoff = ExponentialBackoff(
            base_delay=1.0,
            multiplier=2.0,
            max_delay=60.0,
            jitter=0.0,  # Disable jitter for predictable tests
        )

        # First attempt (attempt=1): 1.0 * 2^0 = 1.0
        assert backoff.get_delay(1) == 1.0
        # Second attempt (attempt=2): 1.0 * 2^1 = 2.0
        assert backoff.get_delay(2) == 2.0
        # Third attempt (attempt=3): 1.0 * 2^2 = 4.0
        assert backoff.get_delay(3) == 4.0

    def test_max_delay_cap(self) -> None:
        """Test delay is capped at max_delay."""
        backoff = ExponentialBackoff(
            base_delay=1.0,
            multiplier=10.0,
            max_delay=5.0,
            jitter=0.0,
        )

        # Should be capped at 5.0
        assert backoff.get_delay(5) == 5.0
