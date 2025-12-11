"""Unit tests for CQRS event_bus.py and command_bus.py.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 2.3**
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest
from hypothesis import given, settings, strategies as st

from application.common.cqrs.commands.command_bus import Command, CommandBus
from application.common.cqrs.events.event_bus import (
    EventHandlerError,
    TypedEventBus,
)
from application.common.cqrs.exceptions.exceptions import HandlerNotFoundError
from core.base.patterns.result import Ok, Result


# Test Events
@dataclass
class TestEvent:
    """Test event for event bus tests."""

    id: str
    data: str


@dataclass
class AnotherEvent:
    """Another test event."""

    value: int


# Test Commands
class TestCommand(Command[str, Exception]):
    """Test command for command bus tests."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def execute(self) -> Result[str, Exception]:
        return Ok(f"Executed: {self.name}")


class TestEventHandler:
    """Test event handler implementation."""

    def __init__(self) -> None:
        self.handled_events: list[Any] = []

    async def handle(self, event: TestEvent) -> None:
        self.handled_events.append(event)


class FailingEventHandler:
    """Event handler that always fails."""

    async def handle(self, event: TestEvent) -> None:
        raise ValueError("Handler failed")


class TestTypedEventBus:
    """Tests for TypedEventBus class."""

    @pytest.fixture()
    def event_bus(self) -> TypedEventBus[TestEvent]:
        """Create event bus."""
        return TypedEventBus()

    @pytest.fixture()
    def handler(self) -> TestEventHandler:
        """Create test handler."""
        return TestEventHandler()

    def test_subscribe_handler(self, event_bus: TypedEventBus[TestEvent], handler: TestEventHandler) -> None:
        """Test subscribing a handler to event type."""
        event_bus.subscribe(TestEvent, handler)

        assert TestEvent in event_bus._handlers
        assert handler in event_bus._handlers[TestEvent]

    def test_unsubscribe_handler(self, event_bus: TypedEventBus[TestEvent], handler: TestEventHandler) -> None:
        """Test unsubscribing a handler from event type."""
        event_bus.subscribe(TestEvent, handler)
        event_bus.unsubscribe(TestEvent, handler)

        assert handler not in event_bus._handlers.get(TestEvent, [])

    def test_unsubscribe_nonexistent_handler(
        self, event_bus: TypedEventBus[TestEvent], handler: TestEventHandler
    ) -> None:
        """Test unsubscribing handler that was never subscribed."""
        # Should not raise
        event_bus.unsubscribe(TestEvent, handler)

    @pytest.mark.asyncio
    async def test_publish_to_single_handler(
        self, event_bus: TypedEventBus[TestEvent], handler: TestEventHandler
    ) -> None:
        """Test publishing event to single subscriber."""
        event_bus.subscribe(TestEvent, handler)
        event = TestEvent(id="1", data="test")

        await event_bus.publish(event)

        assert len(handler.handled_events) == 1
        assert handler.handled_events[0] == event

    @pytest.mark.asyncio
    async def test_publish_to_multiple_handlers(self, event_bus: TypedEventBus[TestEvent]) -> None:
        """Test publishing event to multiple subscribers."""
        handler1 = TestEventHandler()
        handler2 = TestEventHandler()
        event_bus.subscribe(TestEvent, handler1)
        event_bus.subscribe(TestEvent, handler2)
        event = TestEvent(id="1", data="test")

        await event_bus.publish(event)

        assert len(handler1.handled_events) == 1
        assert len(handler2.handled_events) == 1

    @pytest.mark.asyncio
    async def test_publish_no_handlers(self, event_bus: TypedEventBus[TestEvent]) -> None:
        """Test publishing event with no subscribers."""
        event = TestEvent(id="1", data="test")

        # Should not raise
        errors = await event_bus.publish(event, raise_on_error=False)

        assert errors == []

    @pytest.mark.asyncio
    async def test_publish_handler_error_raises(self, event_bus: TypedEventBus[TestEvent]) -> None:
        """Test publishing raises EventHandlerError on handler failure."""
        failing_handler = FailingEventHandler()
        event_bus.subscribe(TestEvent, failing_handler)
        event = TestEvent(id="1", data="test")

        with pytest.raises(EventHandlerError) as exc_info:
            await event_bus.publish(event, raise_on_error=True)

        assert exc_info.value.event_type == "TestEvent"
        assert len(exc_info.value.handler_errors) == 1

    @pytest.mark.asyncio
    async def test_publish_handler_error_returns_errors(self, event_bus: TypedEventBus[TestEvent]) -> None:
        """Test publishing returns errors when raise_on_error=False."""
        failing_handler = FailingEventHandler()
        event_bus.subscribe(TestEvent, failing_handler)
        event = TestEvent(id="1", data="test")

        errors = await event_bus.publish(event, raise_on_error=False)

        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)


class TestCommandBus:
    """Tests for CommandBus class."""

    @pytest.fixture()
    def command_bus(self) -> CommandBus:
        """Create command bus."""
        return CommandBus()

    @pytest.fixture()
    def handler(self) -> AsyncMock:
        """Create mock handler."""
        handler = AsyncMock()
        handler.return_value = Ok("success")
        return handler

    def test_register_handler(self, command_bus: CommandBus, handler: AsyncMock) -> None:
        """Test registering a command handler."""
        command_bus.register(TestCommand, handler)

        assert TestCommand in command_bus._handlers

    def test_register_duplicate_handler_raises(self, command_bus: CommandBus, handler: AsyncMock) -> None:
        """Test registering duplicate handler raises ValueError."""
        command_bus.register(TestCommand, handler)

        with pytest.raises(ValueError, match="Handler already registered"):
            command_bus.register(TestCommand, handler)

    def test_unregister_handler(self, command_bus: CommandBus, handler: AsyncMock) -> None:
        """Test unregistering a command handler."""
        command_bus.register(TestCommand, handler)
        command_bus.unregister(TestCommand)

        assert TestCommand not in command_bus._handlers

    def test_unregister_nonexistent_handler(self, command_bus: CommandBus) -> None:
        """Test unregistering handler that doesn't exist."""
        # Should not raise
        command_bus.unregister(TestCommand)

    @pytest.mark.asyncio
    async def test_dispatch_command(self, command_bus: CommandBus, handler: AsyncMock) -> None:
        """Test dispatching a command to its handler."""
        command_bus.register(TestCommand, handler)
        command = TestCommand(name="test")

        result = await command_bus.dispatch(command)

        assert result.is_ok()
        handler.assert_called_once_with(command)

    @pytest.mark.asyncio
    async def test_dispatch_no_handler_raises(self, command_bus: CommandBus) -> None:
        """Test dispatching command with no handler raises error."""
        command = TestCommand(name="test")

        with pytest.raises(HandlerNotFoundError):
            await command_bus.dispatch(command)

    def test_add_middleware(self, command_bus: CommandBus) -> None:
        """Test adding middleware to command bus."""
        middleware = AsyncMock()
        command_bus.add_middleware(middleware)

        assert middleware in command_bus._middleware

    @pytest.mark.asyncio
    async def test_middleware_execution(self, command_bus: CommandBus, handler: AsyncMock) -> None:
        """Test middleware is executed in order."""
        execution_order: list[str] = []

        async def middleware1(cmd: Any, next_handler: Any) -> Any:
            execution_order.append("middleware1_before")
            result = await next_handler(cmd)
            execution_order.append("middleware1_after")
            return result

        async def middleware2(cmd: Any, next_handler: Any) -> Any:
            execution_order.append("middleware2_before")
            result = await next_handler(cmd)
            execution_order.append("middleware2_after")
            return result

        command_bus.add_middleware(middleware1)
        command_bus.add_middleware(middleware2)
        command_bus.register(TestCommand, handler)

        await command_bus.dispatch(TestCommand(name="test"))

        assert execution_order == [
            "middleware1_before",
            "middleware2_before",
            "middleware2_after",
            "middleware1_after",
        ]

    def test_on_event_handler(self, command_bus: CommandBus) -> None:
        """Test registering event handler."""
        event_handler = AsyncMock()
        command_bus.on_event(event_handler)

        assert event_handler in command_bus._event_handlers


class TestEventBusProperties:
    """Property-based tests for EventBus.

    **Feature: test-coverage-80-percent-v3, Property 3: CQRS Event Bus Publishing**
    **Validates: Requirements 2.3**
    """

    @given(
        event_id=st.text(min_size=1, max_size=20),
        event_data=st.text(min_size=1, max_size=100),
        num_handlers=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_all_handlers_receive_event(self, event_id: str, event_data: str, num_handlers: int) -> None:
        """Property: All subscribed handlers receive the published event.

        **Feature: test-coverage-80-percent-v3, Property 3: CQRS Event Bus Publishing**
        **Validates: Requirements 2.3**
        """
        event_bus: TypedEventBus[TestEvent] = TypedEventBus()
        handlers = [TestEventHandler() for _ in range(num_handlers)]

        for handler in handlers:
            event_bus.subscribe(TestEvent, handler)

        event = TestEvent(id=event_id, data=event_data)
        await event_bus.publish(event, raise_on_error=False)

        for handler in handlers:
            assert len(handler.handled_events) == 1
            assert handler.handled_events[0].id == event_id
            assert handler.handled_events[0].data == event_data


class TestCommandBusProperties:
    """Property-based tests for CommandBus.

    **Feature: test-coverage-80-percent-v3, Property 2: CQRS Command Bus Dispatch**
    **Validates: Requirements 2.3**
    """

    @given(command_name=st.text(min_size=1, max_size=50))
    @settings(max_examples=100, deadline=5000)
    @pytest.mark.asyncio
    async def test_handler_called_exactly_once(self, command_name: str) -> None:
        """Property: Registered handler is called exactly once per dispatch.

        **Feature: test-coverage-80-percent-v3, Property 2: CQRS Command Bus Dispatch**
        **Validates: Requirements 2.3**
        """
        command_bus = CommandBus()
        call_count = 0

        async def counting_handler(cmd: TestCommand) -> Result[str, Exception]:
            nonlocal call_count
            call_count += 1
            return Ok(f"Handled: {cmd.name}")

        command_bus.register(TestCommand, counting_handler)
        command = TestCommand(name=command_name)

        await command_bus.dispatch(command)

        assert call_count == 1
