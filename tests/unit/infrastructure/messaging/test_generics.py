"""Tests for messaging generics module.

**Feature: realistic-test-coverage**
**Validates: Requirements 15.1, 15.2, 15.3**
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from infrastructure.messaging.generics import (
    DeadLetter,
    EventBus,
    FilteredSubscription,
    InMemoryBroker,
    InMemoryDLQ,
    Subscription,
)


@dataclass
class SampleEvent:
    """Sample event for testing."""

    name: str
    value: int = 0


@dataclass
class AnotherEvent:
    """Another event type for testing."""

    message: str


class SampleHandler:
    """Sample event handler."""

    def __init__(self) -> None:
        self.handled_events: list = []

    async def handle(self, event: SampleEvent) -> None:
        self.handled_events.append(event)


class TestEventBus:
    """Tests for EventBus."""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self) -> None:
        """Test subscribing and publishing events."""
        bus = EventBus[SampleEvent]()
        handler = SampleHandler()

        bus.subscribe(SampleEvent, handler)
        await bus.publish(SampleEvent(name="test", value=42))

        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].name == "test"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self) -> None:
        """Test multiple handlers for same event."""
        bus = EventBus[SampleEvent]()
        handler1 = SampleHandler()
        handler2 = SampleHandler()

        bus.subscribe(SampleEvent, handler1)
        bus.subscribe(SampleEvent, handler2)
        await bus.publish(SampleEvent(name="test"))

        assert len(handler1.handled_events) == 1
        assert len(handler2.handled_events) == 1

    @pytest.mark.asyncio
    async def test_subscribe_all(self) -> None:
        """Test subscribing to all events."""
        bus = EventBus[SampleEvent]()
        handler = SampleHandler()

        bus.subscribe_all(handler)
        await bus.publish(SampleEvent(name="event1"))
        await bus.publish(SampleEvent(name="event2"))

        assert len(handler.handled_events) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        """Test unsubscribing handler."""
        bus = EventBus[SampleEvent]()
        handler = SampleHandler()

        bus.subscribe(SampleEvent, handler)
        bus.unsubscribe(SampleEvent, handler)
        await bus.publish(SampleEvent(name="test"))

        assert len(handler.handled_events) == 0

    @pytest.mark.asyncio
    async def test_publish_no_handlers(self) -> None:
        """Test publishing with no handlers."""
        bus = EventBus[SampleEvent]()
        # Should not raise
        await bus.publish(SampleEvent(name="test"))


class TestSubscription:
    """Tests for Subscription."""

    @pytest.mark.asyncio
    async def test_handle_without_filter(self) -> None:
        """Test handling event without filter."""
        handled = []

        async def handler(event: SampleEvent) -> None:
            handled.append(event)

        sub = Subscription(
            event_type=SampleEvent,
            handler=handler,
            filter_fn=None,
        )
        await sub.handle(SampleEvent(name="test"))

        assert len(handled) == 1

    @pytest.mark.asyncio
    async def test_handle_with_passing_filter(self) -> None:
        """Test handling event with passing filter."""
        handled = []

        async def handler(event: SampleEvent) -> None:
            handled.append(event)

        sub = Subscription(
            event_type=SampleEvent,
            handler=handler,
            filter_fn=lambda e: e.value > 10,
        )
        await sub.handle(SampleEvent(name="test", value=20))

        assert len(handled) == 1

    @pytest.mark.asyncio
    async def test_handle_with_failing_filter(self) -> None:
        """Test handling event with failing filter."""
        handled = []

        async def handler(event: SampleEvent) -> None:
            handled.append(event)

        sub = Subscription(
            event_type=SampleEvent,
            handler=handler,
            filter_fn=lambda e: e.value > 10,
        )
        await sub.handle(SampleEvent(name="test", value=5))

        assert len(handled) == 0


class TestFilteredSubscription:
    """Tests for FilteredSubscription."""

    @pytest.mark.asyncio
    async def test_handle_with_config(self) -> None:
        """Test handling with filter config."""
        handled = []

        async def handler(event: SampleEvent) -> None:
            handled.append(event)

        @dataclass
        class FilterConfig:
            min_value: int

        sub = FilteredSubscription(
            event_type=SampleEvent,
            handler=handler,
            filter_config=FilterConfig(min_value=10),
            predicate=lambda e, c: e.value >= c.min_value,
        )
        await sub.handle(SampleEvent(name="test", value=15))

        assert len(handled) == 1

    @pytest.mark.asyncio
    async def test_handle_filtered_out(self) -> None:
        """Test event filtered out by predicate."""
        handled = []

        async def handler(event: SampleEvent) -> None:
            handled.append(event)

        @dataclass
        class FilterConfig:
            min_value: int

        sub = FilteredSubscription(
            event_type=SampleEvent,
            handler=handler,
            filter_config=FilterConfig(min_value=10),
            predicate=lambda e, c: e.value >= c.min_value,
        )
        await sub.handle(SampleEvent(name="test", value=5))

        assert len(handled) == 0


class TestInMemoryBroker:
    """Tests for InMemoryBroker."""

    @pytest.mark.asyncio
    async def test_publish_stores_message(self) -> None:
        """Test that publish stores message."""
        broker = InMemoryBroker[SampleEvent]()
        event = SampleEvent(name="test")

        await broker.publish("topic1", event)

        messages = broker.get_messages("topic1")
        assert len(messages) == 1
        assert messages[0].name == "test"

    @pytest.mark.asyncio
    async def test_subscribe_receives_messages(self) -> None:
        """Test that subscriber receives messages."""
        broker = InMemoryBroker[SampleEvent]()
        handler = AsyncMock()

        await broker.subscribe("topic1", handler)
        await broker.publish("topic1", SampleEvent(name="test"))

        handler.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        """Test unsubscribing from topic."""
        broker = InMemoryBroker[SampleEvent]()
        handler = AsyncMock()

        await broker.subscribe("topic1", handler)
        await broker.unsubscribe("topic1")
        await broker.publish("topic1", SampleEvent(name="test"))

        handler.handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_all_messages(self) -> None:
        """Test getting all messages."""
        broker = InMemoryBroker[SampleEvent]()

        await broker.publish("topic1", SampleEvent(name="event1"))
        await broker.publish("topic2", SampleEvent(name="event2"))

        messages = broker.get_messages()
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_get_messages_by_topic(self) -> None:
        """Test getting messages filtered by topic."""
        broker = InMemoryBroker[SampleEvent]()

        await broker.publish("topic1", SampleEvent(name="event1"))
        await broker.publish("topic2", SampleEvent(name="event2"))

        messages = broker.get_messages("topic1")
        assert len(messages) == 1
        assert messages[0].name == "event1"


class TestDeadLetter:
    """Tests for DeadLetter dataclass."""

    def test_create_dead_letter(self) -> None:
        """Test creating a dead letter."""
        event = SampleEvent(name="failed")
        dl = DeadLetter(
            message=event,
            error="Processing failed",
            retry_count=3,
            first_failure=datetime.now(UTC),
        )
        assert dl.message == event
        assert dl.error == "Processing failed"
        assert dl.retry_count == 3

    def test_dead_letter_with_metadata(self) -> None:
        """Test dead letter with metadata."""
        dl = DeadLetter(
            message=SampleEvent(name="test"),
            error="Error",
            retry_count=1,
            first_failure=datetime.now(UTC),
            metadata={"source": "api", "user_id": "123"},
        )
        assert dl.metadata["source"] == "api"


class TestInMemoryDLQ:
    """Tests for InMemoryDLQ."""

    @pytest.mark.asyncio
    async def test_enqueue(self) -> None:
        """Test enqueueing dead letter."""
        dlq = InMemoryDLQ[SampleEvent]()
        dl = DeadLetter(
            message=SampleEvent(name="test"),
            error="Error",
            retry_count=1,
            first_failure=datetime.now(UTC),
        )

        await dlq.enqueue(dl)

        assert dlq.size == 1

    @pytest.mark.asyncio
    async def test_dequeue(self) -> None:
        """Test dequeueing dead letter."""
        dlq = InMemoryDLQ[SampleEvent]()
        dl = DeadLetter(
            message=SampleEvent(name="test"),
            error="Error",
            retry_count=1,
            first_failure=datetime.now(UTC),
        )

        await dlq.enqueue(dl)
        result = await dlq.dequeue()

        assert result is not None
        assert result.message.name == "test"
        assert dlq.size == 0

    @pytest.mark.asyncio
    async def test_dequeue_empty(self) -> None:
        """Test dequeueing from empty queue."""
        dlq = InMemoryDLQ[SampleEvent]()
        result = await dlq.dequeue()
        assert result is None

    @pytest.mark.asyncio
    async def test_peek(self) -> None:
        """Test peeking at queue."""
        dlq = InMemoryDLQ[SampleEvent]()
        for i in range(5):
            dl = DeadLetter(
                message=SampleEvent(name=f"event{i}"),
                error="Error",
                retry_count=1,
                first_failure=datetime.now(UTC),
            )
            await dlq.enqueue(dl)

        result = await dlq.peek(3)

        assert len(result) == 3
        assert dlq.size == 5  # Queue unchanged

    @pytest.mark.asyncio
    async def test_retry_stub(self) -> None:
        """Test retry returns False (stub)."""
        dlq = InMemoryDLQ[SampleEvent]()
        result = await dlq.retry("some-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_discard_stub(self) -> None:
        """Test discard returns False (stub)."""
        dlq = InMemoryDLQ[SampleEvent]()
        result = await dlq.discard("some-id")
        assert result is False
