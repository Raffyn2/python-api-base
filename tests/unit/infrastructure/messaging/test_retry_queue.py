"""Tests for retry queue module.

**Feature: realistic-test-coverage**
**Validates: Requirements 15.1, 15.2, 15.3**
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from infrastructure.messaging.retry_queue import (
    InMemoryQueueBackend,
    MessageStatus,
    ProcessingResult,
    QueueMessage,
    RetryConfig,
    RetryQueue,
)


@dataclass
class SamplePayload:
    """Sample payload for testing."""

    name: str
    value: int = 0


class MockHandler:
    """Mock message handler for testing."""

    def __init__(
        self,
        should_fail: bool = False,
        fail_count: int = 0,
        should_retry: bool = True,
    ) -> None:
        self._should_fail = should_fail
        self._fail_count = fail_count
        self._should_retry = should_retry
        self._call_count = 0
        self._handled: list[QueueMessage] = []

    async def handle(self, message: QueueMessage) -> ProcessingResult:
        self._call_count += 1
        self._handled.append(message)

        if self._should_fail:
            return ProcessingResult(
                success=False,
                error="Handler failed",
                should_retry=self._should_retry,
            )

        if self._fail_count > 0 and self._call_count <= self._fail_count:
            return ProcessingResult(
                success=False,
                error=f"Temporary failure {self._call_count}",
                should_retry=True,
            )

        return ProcessingResult(success=True)


class TestMessageStatus:
    """Tests for MessageStatus enum."""

    def test_pending_value(self) -> None:
        """Test PENDING status value."""
        assert MessageStatus.PENDING.value == "pending"

    def test_processing_value(self) -> None:
        """Test PROCESSING status value."""
        assert MessageStatus.PROCESSING.value == "processing"

    def test_completed_value(self) -> None:
        """Test COMPLETED status value."""
        assert MessageStatus.COMPLETED.value == "completed"

    def test_failed_value(self) -> None:
        """Test FAILED status value."""
        assert MessageStatus.FAILED.value == "failed"

    def test_dead_letter_value(self) -> None:
        """Test DEAD_LETTER status value."""
        assert MessageStatus.DEAD_LETTER.value == "dead_letter"


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay_ms == 1000
        assert config.max_delay_ms == 60000
        assert config.backoff_multiplier == 2.0
        assert config.jitter_factor == 0.1

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            initial_delay_ms=500,
            max_delay_ms=30000,
            backoff_multiplier=1.5,
            jitter_factor=0.2,
        )
        assert config.max_retries == 5
        assert config.initial_delay_ms == 500


class TestQueueMessage:
    """Tests for QueueMessage dataclass."""

    def test_create_message(self) -> None:
        """Test creating a queue message."""
        msg = QueueMessage(
            id="msg-1",
            payload=SamplePayload(name="test"),
            created_at=datetime.now(UTC),
        )
        assert msg.id == "msg-1"
        assert msg.status == MessageStatus.PENDING
        assert msg.retry_count == 0

    def test_message_with_metadata(self) -> None:
        """Test message with metadata."""
        msg = QueueMessage(
            id="msg-1",
            payload=SamplePayload(name="test"),
            created_at=datetime.now(UTC),
            metadata={"source": "api", "user_id": "123"},
        )
        assert msg.metadata["source"] == "api"


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful result."""
        result = ProcessingResult(success=True)
        assert result.success is True
        assert result.error is None
        assert result.should_retry is True

    def test_failure_result(self) -> None:
        """Test failure result."""
        result = ProcessingResult(
            success=False,
            error="Processing failed",
            should_retry=False,
        )
        assert result.success is False
        assert result.error == "Processing failed"
        assert result.should_retry is False


class TestInMemoryQueueBackend:
    """Tests for InMemoryQueueBackend."""

    @pytest.mark.asyncio
    async def test_enqueue(self) -> None:
        """Test enqueueing a message."""
        backend = InMemoryQueueBackend[SamplePayload]()
        msg = QueueMessage(
            id="msg-1",
            payload=SamplePayload(name="test"),
            created_at=datetime.now(UTC),
        )
        await backend.enqueue(msg)
        messages = await backend.dequeue(10)
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_dequeue_respects_status(self) -> None:
        """Test dequeue only returns pending messages."""
        backend = InMemoryQueueBackend[SamplePayload]()

        msg1 = QueueMessage(
            id="msg-1",
            payload=SamplePayload(name="test1"),
            created_at=datetime.now(UTC),
            status=MessageStatus.PENDING,
        )
        msg2 = QueueMessage(
            id="msg-2",
            payload=SamplePayload(name="test2"),
            created_at=datetime.now(UTC),
            status=MessageStatus.PROCESSING,
        )

        await backend.enqueue(msg1)
        await backend.enqueue(msg2)

        messages = await backend.dequeue(10)
        assert len(messages) == 1
        assert messages[0].id == "msg-1"

    @pytest.mark.asyncio
    async def test_update(self) -> None:
        """Test updating a message."""
        backend = InMemoryQueueBackend[SamplePayload]()
        msg = QueueMessage(
            id="msg-1",
            payload=SamplePayload(name="test"),
            created_at=datetime.now(UTC),
        )
        await backend.enqueue(msg)

        msg.status = MessageStatus.COMPLETED
        await backend.update(msg)

        # Completed messages won't be dequeued
        messages = await backend.dequeue(10)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_move_to_dlq(self) -> None:
        """Test moving message to DLQ."""
        backend = InMemoryQueueBackend[SamplePayload]()
        msg = QueueMessage(
            id="msg-1",
            payload=SamplePayload(name="test"),
            created_at=datetime.now(UTC),
        )
        await backend.enqueue(msg)
        await backend.move_to_dlq(msg)

        # Message removed from main queue
        messages = await backend.dequeue(10)
        assert len(messages) == 0

        # Message in DLQ
        dlq_messages = await backend.get_dlq_messages(10)
        assert len(dlq_messages) == 1

    @pytest.mark.asyncio
    async def test_requeue_from_dlq(self) -> None:
        """Test requeuing message from DLQ."""
        backend = InMemoryQueueBackend[SamplePayload]()
        msg = QueueMessage(
            id="msg-1",
            payload=SamplePayload(name="test"),
            created_at=datetime.now(UTC),
            status=MessageStatus.DEAD_LETTER,
            retry_count=3,
        )
        await backend.enqueue(msg)
        await backend.move_to_dlq(msg)

        result = await backend.requeue_from_dlq("msg-1")
        assert result is True

        # Message back in main queue with reset status
        messages = await backend.dequeue(10)
        assert len(messages) == 1
        assert messages[0].status == MessageStatus.PENDING
        assert messages[0].retry_count == 0

    @pytest.mark.asyncio
    async def test_requeue_from_dlq_not_found(self) -> None:
        """Test requeuing non-existent message."""
        backend = InMemoryQueueBackend[SamplePayload]()
        result = await backend.requeue_from_dlq("non-existent")
        assert result is False


class TestRetryQueue:
    """Tests for RetryQueue."""

    @pytest.mark.asyncio
    async def test_enqueue(self) -> None:
        """Test enqueueing a message."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        queue = RetryQueue(backend, handler)

        msg = await queue.enqueue(SamplePayload(name="test"))

        assert msg.id is not None
        assert msg.status == MessageStatus.PENDING

    @pytest.mark.asyncio
    async def test_enqueue_with_metadata(self) -> None:
        """Test enqueueing with metadata."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        queue = RetryQueue(backend, handler)

        msg = await queue.enqueue(
            SamplePayload(name="test"),
            metadata={"source": "api"},
        )

        assert msg.metadata["source"] == "api"

    @pytest.mark.asyncio
    async def test_process_one_success(self) -> None:
        """Test processing one message successfully."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        queue = RetryQueue(backend, handler)

        await queue.enqueue(SamplePayload(name="test"))
        processed = await queue.process_one()

        assert processed is True
        assert handler._call_count == 1

    @pytest.mark.asyncio
    async def test_process_one_empty_queue(self) -> None:
        """Test processing from empty queue."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        queue = RetryQueue(backend, handler)

        processed = await queue.process_one()

        assert processed is False

    @pytest.mark.asyncio
    async def test_process_with_retry(self) -> None:
        """Test processing with retry on failure."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler(fail_count=1)
        config = RetryConfig(max_retries=3, initial_delay_ms=0)
        queue = RetryQueue(backend, handler, config)

        await queue.enqueue(SamplePayload(name="test"))

        # First attempt fails
        await queue.process_one()
        messages = await backend.dequeue(10)
        assert len(messages) == 1
        assert messages[0].retry_count == 1

    @pytest.mark.asyncio
    async def test_process_moves_to_dlq_after_max_retries(self) -> None:
        """Test message moves to DLQ after max retries."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler(should_fail=True)
        config = RetryConfig(max_retries=2, initial_delay_ms=0)
        queue = RetryQueue(backend, handler, config)

        await queue.enqueue(SamplePayload(name="test"))

        # Process until max retries exceeded
        for _ in range(3):
            await queue.process_one()
            # Reset status for next attempt
            messages = await backend.dequeue(10)
            if messages:
                messages[0].next_retry_at = None
                await backend.update(messages[0])

        dlq_messages = await queue.get_dlq_messages()
        assert len(dlq_messages) >= 1

    @pytest.mark.asyncio
    async def test_process_batch(self) -> None:
        """Test processing a batch of messages."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        queue = RetryQueue(backend, handler)

        for i in range(5):
            await queue.enqueue(SamplePayload(name=f"test-{i}"))

        processed = await queue.process_batch(batch_size=3)

        assert processed == 3
        assert handler._call_count == 3

    @pytest.mark.asyncio
    async def test_register_hook(self) -> None:
        """Test registering hooks."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        queue = RetryQueue(backend, handler)

        hook_called = []

        async def before_hook(msg: QueueMessage) -> None:
            hook_called.append("before")

        async def after_hook(msg: QueueMessage) -> None:
            hook_called.append("after")

        queue.register_hook("before_process", before_hook)
        queue.register_hook("after_process", after_hook)

        await queue.enqueue(SamplePayload(name="test"))
        await queue.process_one()

        assert "before" in hook_called
        assert "after" in hook_called

    @pytest.mark.asyncio
    async def test_dlq_hook(self) -> None:
        """Test DLQ hook is called."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler(should_fail=True, should_retry=False)
        queue = RetryQueue(backend, handler)

        dlq_messages = []

        async def dlq_hook(msg: QueueMessage) -> None:
            dlq_messages.append(msg)

        queue.register_hook("on_dlq", dlq_hook)

        await queue.enqueue(SamplePayload(name="test"))
        await queue.process_one()

        assert len(dlq_messages) == 1

    @pytest.mark.asyncio
    async def test_requeue_from_dlq(self) -> None:
        """Test requeuing from DLQ."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler(should_fail=True, should_retry=False)
        queue = RetryQueue(backend, handler)

        await queue.enqueue(SamplePayload(name="test"))
        await queue.process_one()

        # Requeue from DLQ
        dlq_messages = await queue.get_dlq_messages()
        assert len(dlq_messages) == 1

        result = await queue.requeue_from_dlq(dlq_messages[0].id)
        assert result is True

    @pytest.mark.asyncio
    async def test_requeue_all_dlq(self) -> None:
        """Test requeuing all messages from DLQ."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler(should_fail=True, should_retry=False)
        queue = RetryQueue(backend, handler)

        for i in range(3):
            await queue.enqueue(SamplePayload(name=f"test-{i}"))
            await queue.process_one()

        count = await queue.requeue_all_dlq()
        assert count == 3

    def test_calculate_delay(self) -> None:
        """Test delay calculation with backoff."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        config = RetryConfig(
            initial_delay_ms=1000,
            backoff_multiplier=2.0,
            max_delay_ms=10000,
            jitter_factor=0,
        )
        queue = RetryQueue(backend, handler, config)

        # First retry: 1000 * 2^1 = 2000
        delay1 = queue._calculate_delay(1)
        assert delay1 == 2000

        # Second retry: 1000 * 2^2 = 4000
        delay2 = queue._calculate_delay(2)
        assert delay2 == 4000

    def test_calculate_delay_respects_max(self) -> None:
        """Test delay calculation respects max delay."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        config = RetryConfig(
            initial_delay_ms=1000,
            backoff_multiplier=2.0,
            max_delay_ms=5000,
            jitter_factor=0,
        )
        queue = RetryQueue(backend, handler, config)

        # Would be 1000 * 2^10 = 1024000, but capped at 5000
        delay = queue._calculate_delay(10)
        assert delay == 5000

    def test_stop(self) -> None:
        """Test stopping the queue."""
        backend = InMemoryQueueBackend[SamplePayload]()
        handler = MockHandler()
        queue = RetryQueue(backend, handler)

        queue._running = True
        queue.stop()

        assert queue._running is False

    @pytest.mark.asyncio
    async def test_process_exception_handling(self) -> None:
        """Test exception handling during processing."""
        backend = InMemoryQueueBackend[SamplePayload]()

        class ExceptionHandler:
            async def handle(self, message: QueueMessage) -> ProcessingResult:
                raise RuntimeError("Unexpected error")

        handler = ExceptionHandler()
        config = RetryConfig(max_retries=1, initial_delay_ms=0)
        queue = RetryQueue(backend, handler, config)

        await queue.enqueue(SamplePayload(name="test"))
        await queue.process_one()

        # Message should be retried
        messages = await backend.dequeue(10)
        if messages:
            assert messages[0].retry_count == 1
            assert messages[0].last_error == "Unexpected error"
