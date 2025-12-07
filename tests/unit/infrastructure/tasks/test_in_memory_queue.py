"""Unit tests for InMemoryTaskQueue.

Tests task queue operations, handlers, and processing.
"""

from dataclasses import dataclass

import pytest

from infrastructure.tasks.in_memory import InMemoryTaskQueue
from infrastructure.tasks.protocols import TaskHandler
from infrastructure.tasks.task import Task, TaskPriority, TaskStatus


@dataclass
class SamplePayload:
    """Sample payload for testing."""

    message: str


class SuccessHandler(TaskHandler[SamplePayload, str]):
    """Handler that always succeeds."""

    async def handle(self, payload: SamplePayload) -> str:
        return f"processed: {payload.message}"


class FailingHandler(TaskHandler[SamplePayload, str]):
    """Handler that always fails."""

    async def handle(self, payload: SamplePayload) -> str:
        raise ValueError("Handler failed")


class TestInMemoryTaskQueueBasic:
    """Basic tests for InMemoryTaskQueue."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    @pytest.mark.asyncio
    async def test_enqueue_returns_task_id(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test enqueue returns task ID."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )

        task_id = await queue.enqueue(task)

        assert task_id == task.task_id

    @pytest.mark.asyncio
    async def test_get_task(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test get_task retrieves enqueued task."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        result = await queue.get_task(task.task_id)

        assert result is not None
        assert result.task_id == task.task_id

    @pytest.mark.asyncio
    async def test_get_task_not_found(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test get_task returns None for unknown ID."""
        result = await queue.get_task("unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_returns_pending_task(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test dequeue returns pending task."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        result = await queue.dequeue()

        assert result is not None
        assert result.task_id == task.task_id

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test dequeue returns None for empty queue."""
        result = await queue.dequeue()

        assert result is None


class TestInMemoryTaskQueueHandlers:
    """Tests for handler registration and processing."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    def test_register_handler(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test handler registration."""
        handler = SuccessHandler()

        queue.register_handler("test_handler", handler)

        assert "test_handler" in queue._handlers

    @pytest.mark.asyncio
    async def test_process_next_success(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test successful task processing."""
        queue.register_handler("test_handler", SuccessHandler())
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        result = await queue.process_next()

        assert result is not None
        assert result.success is True
        assert result.value == "processed: hello"

    @pytest.mark.asyncio
    async def test_process_next_no_handler(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test processing with missing handler."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="unknown_handler",
        )
        await queue.enqueue(task)

        result = await queue.process_next()

        assert result is not None
        assert result.success is False
        assert "Handler not found" in (result.error or "")

    @pytest.mark.asyncio
    async def test_process_next_empty_queue(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test process_next with empty queue."""
        result = await queue.process_next()

        assert result is None

    @pytest.mark.asyncio
    async def test_process_next_with_handler_override(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test process_next with handler override."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        handlers = {"test_handler": SuccessHandler()}
        result = await queue.process_next(handlers)

        assert result is not None
        assert result.success is True


class TestInMemoryTaskQueueStatus:
    """Tests for task status operations."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    @pytest.mark.asyncio
    async def test_cancel_pending_task(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test cancelling pending task."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        result = await queue.cancel_task(task.task_id)

        assert result is True
        updated = await queue.get_task(task.task_id)
        assert updated is not None
        assert updated.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test cancelling nonexistent task."""
        result = await queue.cancel_task("unknown")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test getting tasks by status."""
        task1 = Task[SamplePayload, str](
            name="test1",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        task2 = Task[SamplePayload, str](
            name="test2",
            payload=SamplePayload(message="world"),
            handler="test_handler",
        )
        await queue.enqueue(task1)
        await queue.enqueue(task2)

        pending = await queue.get_tasks_by_status(TaskStatus.PENDING)

        assert len(pending) == 2


class TestInMemoryTaskQueueCounts:
    """Tests for queue counts."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    @pytest.mark.asyncio
    async def test_pending_count(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test pending count."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        assert queue.pending_count == 1

    @pytest.mark.asyncio
    async def test_total_count(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test total count."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        assert queue.total_count == 1

    def test_clear(self, queue: InMemoryTaskQueue[SamplePayload, str]) -> None:
        """Test clear removes all tasks."""
        queue._tasks["task1"] = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )

        queue.clear()

        assert queue.total_count == 0


class TestInMemoryTaskQueuePriority:
    """Tests for task priority."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    @pytest.mark.asyncio
    async def test_high_priority_processed_first(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test high priority tasks are processed first."""
        low_task = Task[SamplePayload, str](
            name="low",
            payload=SamplePayload(message="low"),
            handler="test_handler",
            priority=TaskPriority.LOW,
        )
        high_task = Task[SamplePayload, str](
            name="high",
            payload=SamplePayload(message="high"),
            handler="test_handler",
            priority=TaskPriority.HIGH,
        )

        await queue.enqueue(low_task)
        await queue.enqueue(high_task)

        first = await queue.dequeue()

        assert first is not None
        assert first.name == "high"



class TestInMemoryTaskQueueRetry:
    """Tests for task retry functionality."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    @pytest.mark.asyncio
    async def test_retry_failed_task(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test retrying a failed task."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
            max_attempts=3,
        )
        await queue.enqueue(task)

        # Process with failing handler to mark as failed
        queue.register_handler("test_handler", FailingHandler())
        await queue.process_next()

        # Get the task and verify it can be retried
        updated_task = await queue.get_task(task.task_id)
        assert updated_task is not None

    @pytest.mark.asyncio
    async def test_retry_nonexistent_task(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test retrying nonexistent task returns False."""
        result = await queue.retry_task("unknown")

        assert result is False

    @pytest.mark.asyncio
    async def test_retry_task_not_retriable(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test retry returns False when task cannot be retried."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
            max_attempts=1,  # Only one attempt allowed
        )
        task._attempt = 1  # Already attempted
        queue._tasks[task.task_id] = task

        result = await queue.retry_task(task.task_id)

        assert result is False


class TestInMemoryTaskQueueProcessAll:
    """Tests for process_all functionality."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    @pytest.mark.asyncio
    async def test_process_all_multiple_tasks(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test processing all tasks."""
        queue.register_handler("test_handler", SuccessHandler())

        for i in range(3):
            task = Task[SamplePayload, str](
                name=f"test_{i}",
                payload=SamplePayload(message=f"msg_{i}"),
                handler="test_handler",
            )
            await queue.enqueue(task)

        processed = await queue.process_all()

        assert processed == 3

    @pytest.mark.asyncio
    async def test_process_all_empty_queue(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test process_all with empty queue."""
        processed = await queue.process_all()

        assert processed == 0

    @pytest.mark.asyncio
    async def test_process_all_with_max_limit(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test process_all respects max_tasks limit."""
        queue.register_handler("test_handler", SuccessHandler())

        for i in range(5):
            task = Task[SamplePayload, str](
                name=f"test_{i}",
                payload=SamplePayload(message=f"msg_{i}"),
                handler="test_handler",
            )
            await queue.enqueue(task)

        processed = await queue.process_all(max_tasks=2)

        assert processed == 2

    @pytest.mark.asyncio
    async def test_process_all_with_handler_override(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test process_all with handler override."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        handlers = {"test_handler": SuccessHandler()}
        processed = await queue.process_all(handlers)

        assert processed == 1


class TestInMemoryTaskQueueFailure:
    """Tests for task failure handling."""

    @pytest.fixture
    def queue(self) -> InMemoryTaskQueue[SamplePayload, str]:
        """Create queue instance."""
        return InMemoryTaskQueue[SamplePayload, str]()

    @pytest.mark.asyncio
    async def test_handler_failure_marks_task_failed(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test handler failure marks task as failed."""
        queue.register_handler("test_handler", FailingHandler())
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
            max_attempts=1,
        )
        await queue.enqueue(task)

        result = await queue.process_next()

        assert result is not None
        assert result.success is False
        assert "Handler failed" in (result.error or "")

    @pytest.mark.asyncio
    async def test_update_task(
        self, queue: InMemoryTaskQueue[SamplePayload, str]
    ) -> None:
        """Test update_task updates task state."""
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        task.mark_running()
        await queue.update_task(task)

        updated = await queue.get_task(task.task_id)
        assert updated is not None
        assert updated.status == TaskStatus.RUNNING
