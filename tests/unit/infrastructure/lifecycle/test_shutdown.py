"""Unit tests for shutdown handler.

Tests ShutdownHandler, ShutdownConfig, ShutdownState.
"""

# Import directly to avoid middleware_config import chain
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# Add src to path for direct import
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import the module directly without going through __init__
import importlib.util

spec = importlib.util.spec_from_file_location(
    "shutdown",
    src_path / "infrastructure" / "lifecycle" / "shutdown.py",
)
shutdown_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shutdown_module)

ShutdownConfig = shutdown_module.ShutdownConfig
ShutdownHandler = shutdown_module.ShutdownHandler
ShutdownState = shutdown_module.ShutdownState


class TestShutdownState:
    """Tests for ShutdownState enum."""

    def test_running_value(self) -> None:
        """Test RUNNING value."""
        assert ShutdownState.RUNNING.value == "running"

    def test_shutting_down_value(self) -> None:
        """Test SHUTTING_DOWN value."""
        assert ShutdownState.SHUTTING_DOWN.value == "shutting_down"

    def test_shutdown_value(self) -> None:
        """Test SHUTDOWN value."""
        assert ShutdownState.SHUTDOWN.value == "shutdown"


class TestShutdownConfig:
    """Tests for ShutdownConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ShutdownConfig()
        assert config.timeout == 30.0
        assert config.drain_timeout == 10.0
        assert config.force_exit is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ShutdownConfig(timeout=60.0, drain_timeout=20.0, force_exit=False)
        assert config.timeout == 60.0
        assert config.drain_timeout == 20.0
        assert config.force_exit is False


class TestShutdownHandler:
    """Tests for ShutdownHandler."""

    def test_initial_state(self) -> None:
        """Test handler starts in RUNNING state."""
        handler = ShutdownHandler()
        assert handler.state == ShutdownState.RUNNING
        assert handler.is_shutting_down is False
        assert handler.in_flight_requests == 0

    def test_add_hook(self) -> None:
        """Test adding shutdown hooks."""
        handler = ShutdownHandler()
        hook = AsyncMock()

        handler.add_hook("test", hook)

        status = handler.get_status()
        assert "test" in status["hooks"]
        assert status["hooks_count"] == 1

    def test_add_multiple_hooks(self) -> None:
        """Test adding multiple hooks."""
        handler = ShutdownHandler()

        handler.add_hook("hook1", AsyncMock())
        handler.add_hook("hook2", AsyncMock())
        handler.add_hook("hook3", AsyncMock())

        status = handler.get_status()
        assert status["hooks_count"] == 3

    def test_hooks_sorted_by_priority(self) -> None:
        """Test hooks are sorted by priority (higher first)."""
        handler = ShutdownHandler()

        handler.add_hook("low", AsyncMock(), priority=1)
        handler.add_hook("high", AsyncMock(), priority=10)
        handler.add_hook("medium", AsyncMock(), priority=5)

        status = handler.get_status()
        assert status["hooks"][0] == "high"
        assert status["hooks"][1] == "medium"
        assert status["hooks"][2] == "low"

    def test_remove_hook(self) -> None:
        """Test removing a hook."""
        handler = ShutdownHandler()
        handler.add_hook("test", AsyncMock())

        result = handler.remove_hook("test")

        assert result is True
        assert handler.get_status()["hooks_count"] == 0

    def test_remove_nonexistent_hook(self) -> None:
        """Test removing nonexistent hook returns False."""
        handler = ShutdownHandler()

        result = handler.remove_hook("nonexistent")

        assert result is False

    def test_request_tracking(self) -> None:
        """Test request started/finished tracking."""
        handler = ShutdownHandler()

        handler.request_started()
        assert handler.in_flight_requests == 1

        handler.request_started()
        assert handler.in_flight_requests == 2

        handler.request_finished()
        assert handler.in_flight_requests == 1

        handler.request_finished()
        assert handler.in_flight_requests == 0

    def test_request_finished_not_negative(self) -> None:
        """Test request count doesn't go negative."""
        handler = ShutdownHandler()

        handler.request_finished()
        handler.request_finished()

        assert handler.in_flight_requests == 0

    @pytest.mark.asyncio
    async def test_shutdown_changes_state(self) -> None:
        """Test shutdown changes state to SHUTDOWN."""
        handler = ShutdownHandler()

        await handler.shutdown()

        assert handler.state == ShutdownState.SHUTDOWN

    @pytest.mark.asyncio
    async def test_shutdown_runs_hooks(self) -> None:
        """Test shutdown runs all hooks."""
        handler = ShutdownHandler()
        hook1 = AsyncMock()
        hook2 = AsyncMock()

        handler.add_hook("hook1", hook1)
        handler.add_hook("hook2", hook2)

        await handler.shutdown()

        hook1.assert_called_once()
        hook2.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_idempotent(self) -> None:
        """Test calling shutdown twice doesn't run hooks twice."""
        handler = ShutdownHandler()
        hook = AsyncMock()
        handler.add_hook("test", hook)

        await handler.shutdown()
        await handler.shutdown()

        hook.assert_called_once()

    def test_get_status(self) -> None:
        """Test get_status returns correct info."""
        handler = ShutdownHandler()
        handler.add_hook("test", AsyncMock())
        handler.request_started()

        status = handler.get_status()

        assert status["state"] == "running"
        assert status["in_flight_requests"] == 1
        assert status["hooks_count"] == 1
        assert "test" in status["hooks"]

    def test_is_shutting_down_during_shutdown(self) -> None:
        """Test is_shutting_down returns True during shutdown."""
        handler = ShutdownHandler()
        handler._state = ShutdownState.SHUTTING_DOWN

        assert handler.is_shutting_down is True

    def test_request_not_started_during_shutdown(self) -> None:
        """Test requests not tracked during shutdown."""
        handler = ShutdownHandler()
        handler._state = ShutdownState.SHUTTING_DOWN

        handler.request_started()

        assert handler.in_flight_requests == 0
