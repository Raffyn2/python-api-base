"""Unit tests for TypedEventBus.

Tests event subscription, publishing, and error handling.
"""

from dataclasses import dataclass

import pytest

from application.common.cqrs import (
    EventHandlerError,
    TypedEventBus,
)


@dataclass
class UserCreatedEvent:
    """Test event for user creation."""

    user_id: str
    name: str


@dataclass
class UserDeletedEvent:
    """Test event for user deletion."""

    user_id: str


class UserCreatedHandler:
    """Test handler for UserCreatedEvent."""

    def __init__(self) -> None:
        self.handled_events: list[UserCreatedEvent] = []

    async def handle(self, event: UserCreatedEvent) -> None:
        self.handled_events.append(event)


class FailingHandler:
    """Test handler that always fails."""

    async def handle(self, event: UserCreatedEvent) -> None:
        raise ValueError("Handler failed")


class TestTypedEventBusSubscription:
    """Tests for event subscription."""

    def test_subscribe_handler(self) -> None:
        """Test subscribing a handler to an event type."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler = UserCreatedHandler()

        bus.subscribe(UserCreatedEvent, handler)

        assert UserCreatedEvent in bus._handlers
        assert handler in bus._handlers[UserCreatedEvent]

    def test_subscribe_multiple_handlers(self) -> None:
        """Test subscribing multiple handlers to same event type."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler1 = UserCreatedHandler()
        handler2 = UserCreatedHandler()

        bus.subscribe(UserCreatedEvent, handler1)
        bus.subscribe(UserCreatedEvent, handler2)

        assert len(bus._handlers[UserCreatedEvent]) == 2

    def test_unsubscribe_handler(self) -> None:
        """Test unsubscribing a handler from an event type."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler = UserCreatedHandler()

        bus.subscribe(UserCreatedEvent, handler)
        bus.unsubscribe(UserCreatedEvent, handler)

        assert handler not in bus._handlers.get(UserCreatedEvent, [])

    def test_unsubscribe_nonexistent_handler(self) -> None:
        """Test unsubscribing non-existent handler does not raise."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler = UserCreatedHandler()

        bus.unsubscribe(UserCreatedEvent, handler)  # Should not raise


class TestTypedEventBusPublish:
    """Tests for event publishing."""

    @pytest.mark.asyncio
    async def test_publish_event_to_handler(self) -> None:
        """Test publishing event calls subscribed handler."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler = UserCreatedHandler()
        event = UserCreatedEvent(user_id="123", name="John")

        bus.subscribe(UserCreatedEvent, handler)
        await bus.publish(event)

        assert len(handler.handled_events) == 1
        assert handler.handled_events[0] == event

    @pytest.mark.asyncio
    async def test_publish_event_to_multiple_handlers(self) -> None:
        """Test publishing event calls all subscribed handlers."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler1 = UserCreatedHandler()
        handler2 = UserCreatedHandler()
        event = UserCreatedEvent(user_id="123", name="John")

        bus.subscribe(UserCreatedEvent, handler1)
        bus.subscribe(UserCreatedEvent, handler2)
        await bus.publish(event)

        assert len(handler1.handled_events) == 1
        assert len(handler2.handled_events) == 1

    @pytest.mark.asyncio
    async def test_publish_event_no_handlers(self) -> None:
        """Test publishing event with no handlers does not raise."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        event = UserCreatedEvent(user_id="123", name="John")

        errors = await bus.publish(event)

        assert errors == []

    @pytest.mark.asyncio
    async def test_publish_different_event_types(self) -> None:
        """Test handlers only receive their subscribed event type."""
        bus: TypedEventBus[UserCreatedEvent | UserDeletedEvent] = TypedEventBus()
        created_handler = UserCreatedHandler()

        bus.subscribe(UserCreatedEvent, created_handler)

        await bus.publish(UserCreatedEvent(user_id="123", name="John"))
        await bus.publish(UserDeletedEvent(user_id="456"))

        assert len(created_handler.handled_events) == 1


class TestTypedEventBusErrorHandling:
    """Tests for error handling in event publishing."""

    @pytest.mark.asyncio
    async def test_handler_error_raises_by_default(self) -> None:
        """Test handler error raises EventHandlerError by default."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler = FailingHandler()
        event = UserCreatedEvent(user_id="123", name="John")

        bus.subscribe(UserCreatedEvent, handler)

        with pytest.raises(EventHandlerError) as exc_info:
            await bus.publish(event)

        assert exc_info.value.event_type == "UserCreatedEvent"
        assert len(exc_info.value.handler_errors) == 1

    @pytest.mark.asyncio
    async def test_handler_error_returns_errors_when_disabled(self) -> None:
        """Test handler error returns errors when raise_on_error=False."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler = FailingHandler()
        event = UserCreatedEvent(user_id="123", name="John")

        bus.subscribe(UserCreatedEvent, handler)
        errors = await bus.publish(event, raise_on_error=False)

        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)

    @pytest.mark.asyncio
    async def test_multiple_handler_errors(self) -> None:
        """Test multiple handler errors are collected."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        handler1 = FailingHandler()
        handler2 = FailingHandler()
        event = UserCreatedEvent(user_id="123", name="John")

        bus.subscribe(UserCreatedEvent, handler1)
        bus.subscribe(UserCreatedEvent, handler2)

        with pytest.raises(EventHandlerError) as exc_info:
            await bus.publish(event)

        assert len(exc_info.value.handler_errors) == 2

    @pytest.mark.asyncio
    async def test_partial_handler_failure(self) -> None:
        """Test some handlers succeed while others fail."""
        bus: TypedEventBus[UserCreatedEvent] = TypedEventBus()
        success_handler = UserCreatedHandler()
        failing_handler = FailingHandler()
        event = UserCreatedEvent(user_id="123", name="John")

        bus.subscribe(UserCreatedEvent, success_handler)
        bus.subscribe(UserCreatedEvent, failing_handler)

        errors = await bus.publish(event, raise_on_error=False)

        # Success handler should have processed the event
        assert len(success_handler.handled_events) == 1
        # One error from failing handler
        assert len(errors) == 1


class TestEventHandlerError:
    """Tests for EventHandlerError exception."""

    def test_error_message(self) -> None:
        """Test error message format."""
        error = EventHandlerError(
            event_type="UserCreatedEvent",
            handler_errors=[
                ("Handler1", ValueError("Error 1")),
                ("Handler2", RuntimeError("Error 2")),
            ],
        )

        assert "2 handler(s) failed" in str(error)
        assert "UserCreatedEvent" in str(error)

    def test_error_attributes(self) -> None:
        """Test error attributes are set correctly."""
        handler_errors = [("Handler1", ValueError("Error 1"))]
        error = EventHandlerError(
            event_type="TestEvent",
            handler_errors=handler_errors,
        )

        assert error.event_type == "TestEvent"
        assert error.handler_errors == handler_errors
