"""Unit tests for task protocols.

Tests TaskHandler, TaskQueue, and TaskScheduler protocols.
"""

from dataclasses import dataclass
from datetime import datetime

import pytest

from infrastructure.tasks.protocols import TaskHandler, TaskQueue, TaskScheduler
from infrastructure.tasks.task import Task, TaskStatus


@dataclass
class SamplePayload:
    """Sample payload for testing."""

    message: str


class ConcreteTaskHandler:
    """Concrete implementation of TaskHandler for testing."""

    async def handle(self, payload: SamplePayload) -> str:
        return f"handled: {payload.message}"


class TestTaskHandlerProtocol:
    """Tests for TaskHandler protocol."""

    def test_concrete_handler_is_task_handler(self) -> None:
        """Test concrete handler implements protocol."""
        handler = ConcreteTaskHandler()

        assert isinstance(handler, TaskHandler)

    @pytest.mark.asyncio
    async def test_handler_execution(self) -> None:
        """Test handler can be executed."""
        handler = ConcreteTaskHandler()
        payload = SamplePayload(message="test")

        result = await handler.handle(payload)

        assert result == "handled: test"


class ConcreteTaskQueue:
    """Concrete implementation of TaskQueue for testing."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    async def enqueue(self, task: Task) -> str:
        self._tasks[task.task_id] = task
        return task.task_id

    async def dequeue(self) -> Task | None:
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING:
                return task
        return None

    async def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    async def update_task(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    async def get_tasks_by_status(self, status: TaskStatus, limit: int = 100) -> list[Task]:
        return [t for t in list(self._tasks.values())[:limit] if t.status == status]

    async def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.mark_cancelled()
            return True
        return False

    async def retry_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.can_retry:
            task.status = TaskStatus.PENDING
            return True
        return False


class TestTaskQueueProtocol:
    """Tests for TaskQueue protocol."""

    def test_concrete_queue_is_task_queue(self) -> None:
        """Test concrete queue implements protocol."""
        queue = ConcreteTaskQueue()

        assert isinstance(queue, TaskQueue)

    @pytest.mark.asyncio
    async def test_enqueue_and_get(self) -> None:
        """Test enqueue and get_task."""
        queue = ConcreteTaskQueue()
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )

        task_id = await queue.enqueue(task)
        retrieved = await queue.get_task(task_id)

        assert retrieved is not None
        assert retrieved.task_id == task_id

    @pytest.mark.asyncio
    async def test_dequeue(self) -> None:
        """Test dequeue returns pending task."""
        queue = ConcreteTaskQueue()
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        dequeued = await queue.dequeue()

        assert dequeued is not None
        assert dequeued.task_id == task.task_id

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self) -> None:
        """Test get_tasks_by_status."""
        queue = ConcreteTaskQueue()
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        await queue.enqueue(task)

        pending = await queue.get_tasks_by_status(TaskStatus.PENDING)

        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_cancel_task(self) -> None:
        """Test cancel_task."""
        queue = ConcreteTaskQueue()
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


class ConcreteTaskScheduler:
    """Concrete implementation of TaskScheduler for testing."""

    def __init__(self) -> None:
        self._schedules: dict[str, tuple[Task, datetime | str]] = {}

    async def schedule(self, task: Task, run_at: datetime) -> str:
        schedule_id = f"schedule_{task.task_id}"
        self._schedules[schedule_id] = (task, run_at)
        return schedule_id

    async def schedule_recurring(self, task: Task, cron_expression: str) -> str:
        schedule_id = f"recurring_{task.task_id}"
        self._schedules[schedule_id] = (task, cron_expression)
        return schedule_id

    async def cancel_schedule(self, schedule_id: str) -> bool:
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False


class TestTaskSchedulerProtocol:
    """Tests for TaskScheduler protocol."""

    def test_concrete_scheduler_is_task_scheduler(self) -> None:
        """Test concrete scheduler implements protocol."""
        scheduler = ConcreteTaskScheduler()

        assert isinstance(scheduler, TaskScheduler)

    @pytest.mark.asyncio
    async def test_schedule(self) -> None:
        """Test schedule task."""
        scheduler = ConcreteTaskScheduler()
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        run_at = datetime.now()

        schedule_id = await scheduler.schedule(task, run_at)

        assert schedule_id is not None
        assert schedule_id.startswith("schedule_")

    @pytest.mark.asyncio
    async def test_schedule_recurring(self) -> None:
        """Test schedule recurring task."""
        scheduler = ConcreteTaskScheduler()
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )

        schedule_id = await scheduler.schedule_recurring(task, "0 * * * *")

        assert schedule_id is not None
        assert schedule_id.startswith("recurring_")

    @pytest.mark.asyncio
    async def test_cancel_schedule(self) -> None:
        """Test cancel schedule."""
        scheduler = ConcreteTaskScheduler()
        task = Task[SamplePayload, str](
            name="test",
            payload=SamplePayload(message="hello"),
            handler="test_handler",
        )
        schedule_id = await scheduler.schedule(task, datetime.now())

        result = await scheduler.cancel_schedule(schedule_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_schedule(self) -> None:
        """Test cancel nonexistent schedule."""
        scheduler = ConcreteTaskScheduler()

        result = await scheduler.cancel_schedule("nonexistent")

        assert result is False
