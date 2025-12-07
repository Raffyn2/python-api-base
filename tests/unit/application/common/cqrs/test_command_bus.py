"""Unit tests for CommandBus.

Tests command registration, dispatch, middleware, and event handling.
"""

import pytest

from application.common.cqrs import (
    Command,
    CommandBus,
    HandlerNotFoundError,
)
from core.base.patterns.result import Err, Ok, Result


class CreateUserCommand(Command[str, str]):
    """Test command for creating a user."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.events: list[str] = []

    async def execute(self) -> Result[str, str]:
        return Ok(f"User {self.name} created")


class FailingCommand(Command[str, str]):
    """Test command that fails."""

    async def execute(self) -> Result[str, str]:
        return Err("Command failed")


class TestCommandBusRegistration:
    """Tests for command handler registration."""

    def test_register_handler(self) -> None:
        """Test registering a command handler."""
        bus = CommandBus()

        async def handler(cmd: CreateUserCommand) -> Result[str, str]:
            return Ok(f"Handled {cmd.name}")

        bus.register(CreateUserCommand, handler)
        assert CreateUserCommand in bus._handlers

    def test_register_duplicate_handler_raises(self) -> None:
        """Test that registering duplicate handler raises ValueError."""
        bus = CommandBus()

        async def handler(cmd: CreateUserCommand) -> Result[str, str]:
            return Ok("OK")

        bus.register(CreateUserCommand, handler)

        with pytest.raises(ValueError, match="Handler already registered"):
            bus.register(CreateUserCommand, handler)

    def test_unregister_handler(self) -> None:
        """Test unregistering a command handler."""
        bus = CommandBus()

        async def handler(cmd: CreateUserCommand) -> Result[str, str]:
            return Ok("OK")

        bus.register(CreateUserCommand, handler)
        bus.unregister(CreateUserCommand)
        assert CreateUserCommand not in bus._handlers

    def test_unregister_nonexistent_handler(self) -> None:
        """Test unregistering non-existent handler does not raise."""
        bus = CommandBus()
        bus.unregister(CreateUserCommand)  # Should not raise


class TestCommandBusDispatch:
    """Tests for command dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_command(self) -> None:
        """Test dispatching a command to its handler."""
        bus = CommandBus()
        call_count = 0

        async def handler(cmd: CreateUserCommand) -> Result[str, str]:
            nonlocal call_count
            call_count += 1
            return Ok(f"Created {cmd.name}")

        bus.register(CreateUserCommand, handler)
        result = await bus.dispatch(CreateUserCommand("John"))

        assert call_count == 1
        assert isinstance(result, Ok)
        assert result.value == "Created John"

    @pytest.mark.asyncio
    async def test_dispatch_unregistered_command_raises(self) -> None:
        """Test dispatching unregistered command raises HandlerNotFoundError."""
        bus = CommandBus()

        with pytest.raises(HandlerNotFoundError):
            await bus.dispatch(CreateUserCommand("John"))

    @pytest.mark.asyncio
    async def test_dispatch_returns_error_result(self) -> None:
        """Test dispatching command that returns error."""
        bus = CommandBus()

        async def handler(cmd: FailingCommand) -> Result[str, str]:
            return Err("Failed")

        bus.register(FailingCommand, handler)
        result = await bus.dispatch(FailingCommand())

        assert isinstance(result, Err)
        assert result.error == "Failed"


class TestCommandBusMiddleware:
    """Tests for middleware functionality."""

    def test_add_middleware(self) -> None:
        """Test adding middleware to bus."""
        bus = CommandBus()

        async def middleware(cmd, next_handler):
            return await next_handler(cmd)

        bus.add_middleware(middleware)
        assert len(bus._middleware) == 1

    def test_add_multiple_middleware(self) -> None:
        """Test adding multiple middleware."""
        bus = CommandBus()

        async def middleware1(cmd, next_handler):
            return await next_handler(cmd)

        async def middleware2(cmd, next_handler):
            return await next_handler(cmd)

        bus.add_middleware(middleware1)
        bus.add_middleware(middleware2)
        assert len(bus._middleware) == 2


class TestCommandBusEvents:
    """Tests for event handling."""

    def test_on_event_registers_handler(self) -> None:
        """Test registering event handler."""
        bus = CommandBus()

        async def event_handler(event: str) -> None:
            pass

        bus.on_event(event_handler)
        assert len(bus._event_handlers) == 1

    def test_multiple_event_handlers_registered(self) -> None:
        """Test registering multiple event handlers."""
        bus = CommandBus()

        async def handler1(event: str) -> None:
            pass

        async def handler2(event: str) -> None:
            pass

        bus.on_event(handler1)
        bus.on_event(handler2)
        assert len(bus._event_handlers) == 2
