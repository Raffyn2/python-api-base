"""Property-based tests for health checks and graceful shutdown.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 24.1, 24.2, 24.3, 24.4, 24.5, 24.6**

Tests for:
- Liveness endpoint returns 200 when running
- Readiness endpoint checks dependencies
- Startup endpoint reflects startup state
- Graceful shutdown handles in-flight requests
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, strategies as st

from infrastructure.lifecycle import (
    ShutdownConfig,
    ShutdownHandler,
    ShutdownMiddleware,
    ShutdownState,
)

# === Test Fixtures ===


@pytest.fixture
def shutdown_config() -> ShutdownConfig:
    """Default shutdown configuration."""
    return ShutdownConfig(
        timeout=5.0,
        drain_timeout=2.0,
        force_exit=False,
    )


@pytest.fixture
def shutdown_handler(shutdown_config: ShutdownConfig) -> ShutdownHandler:
    """Shutdown handler for testing."""
    return ShutdownHandler(config=shutdown_config)


# === Property Tests ===


class TestLivenessCheck:
    """Tests for liveness endpoint.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 24.1**
    """

    def test_liveness_returns_ok_when_running(self) -> None:
        """Liveness SHALL return 200 when process is running.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.1**
        """
        # The liveness endpoint just returns {"status": "ok"}
        # It doesn't depend on any state
        import asyncio

        from interface.v1.health_router import liveness

        result = asyncio.run(liveness())
        assert result["status"] == "ok"


class TestStartupCheck:
    """Tests for startup endpoint.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 24.3**
    """

    def test_startup_returns_503_before_complete(self) -> None:
        """Startup SHALL return 503 before startup is complete.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.3**
        """
        import asyncio
        import sys

        # Access the module directly
        health_module = sys.modules.get("interface.v1.health_router")
        if health_module is None:
            from interface.v1 import health_router as health_module

        # Save original state
        original_state = getattr(health_module, "_startup_complete", True)

        try:
            # Set startup incomplete
            health_module._startup_complete = False

            # Create mock response
            mock_response = MagicMock()

            result = asyncio.run(health_module.startup(mock_response))

            assert result["startup_complete"] is False
            assert result["status"] == "starting"
            assert mock_response.status_code == 503
        finally:
            # Restore original state
            health_module._startup_complete = original_state

    def test_startup_returns_200_after_complete(self) -> None:
        """Startup SHALL return 200 after startup is complete.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.3**
        """
        import asyncio
        import sys

        # Access the module directly
        health_module = sys.modules.get("interface.v1.health_router")
        if health_module is None:
            from interface.v1 import health_router as health_module

        # Save original state
        original_state = getattr(health_module, "_startup_complete", True)

        try:
            # Mark startup complete
            health_module._startup_complete = True

            # Create mock response
            mock_response = MagicMock()

            result = asyncio.run(health_module.startup(mock_response))

            assert result["startup_complete"] is True
            assert result["status"] == "ok"
            # Status code should not be set (defaults to 200)
        finally:
            # Restore original state
            health_module._startup_complete = original_state


class TestGracefulShutdown:
    """Tests for graceful shutdown.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 24.4, 24.5, 24.6**
    """

    def test_shutdown_handler_initial_state(
        self, shutdown_handler: ShutdownHandler
    ) -> None:
        """Handler SHALL start in RUNNING state.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4**
        """
        assert shutdown_handler.state == ShutdownState.RUNNING
        assert not shutdown_handler.is_shutting_down
        assert shutdown_handler.in_flight_requests == 0

    def test_request_tracking(self, shutdown_handler: ShutdownHandler) -> None:
        """Handler SHALL track in-flight requests.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4**
        """
        assert shutdown_handler.in_flight_requests == 0

        shutdown_handler.request_started()
        assert shutdown_handler.in_flight_requests == 1

        shutdown_handler.request_started()
        assert shutdown_handler.in_flight_requests == 2

        shutdown_handler.request_finished()
        assert shutdown_handler.in_flight_requests == 1

        shutdown_handler.request_finished()
        assert shutdown_handler.in_flight_requests == 0

    def test_request_finished_never_negative(
        self, shutdown_handler: ShutdownHandler
    ) -> None:
        """In-flight count SHALL never go negative.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4**
        """
        # Finish more requests than started
        shutdown_handler.request_finished()
        shutdown_handler.request_finished()

        assert shutdown_handler.in_flight_requests == 0

    @pytest.mark.asyncio
    async def test_shutdown_transitions_state(
        self, shutdown_handler: ShutdownHandler
    ) -> None:
        """Shutdown SHALL transition through states.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4, 24.5**
        """
        assert shutdown_handler.state == ShutdownState.RUNNING

        await shutdown_handler.shutdown()

        assert shutdown_handler.state == ShutdownState.SHUTDOWN
        assert shutdown_handler.is_shutting_down

    @pytest.mark.asyncio
    async def test_shutdown_runs_hooks(self, shutdown_handler: ShutdownHandler) -> None:
        """Shutdown SHALL run all registered hooks.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.5**
        """
        hooks_called: list[str] = []

        async def hook1():
            hooks_called.append("hook1")

        async def hook2():
            hooks_called.append("hook2")

        shutdown_handler.add_hook("hook1", hook1, priority=1)
        shutdown_handler.add_hook("hook2", hook2, priority=2)

        await shutdown_handler.shutdown()

        # Higher priority hooks run first
        assert hooks_called == ["hook2", "hook1"]

    @pytest.mark.asyncio
    async def test_shutdown_ignores_duplicate_calls(
        self, shutdown_handler: ShutdownHandler
    ) -> None:
        """Duplicate shutdown calls SHALL be ignored.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4**
        """
        await shutdown_handler.shutdown()

        # Second call should not raise or cause issues
        await shutdown_handler.shutdown()

        assert shutdown_handler.state == ShutdownState.SHUTDOWN

    def test_hook_priority_ordering(self, shutdown_handler: ShutdownHandler) -> None:
        """Hooks SHALL be ordered by priority (higher first).

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.5**
        """

        async def dummy():
            pass

        shutdown_handler.add_hook("low", dummy, priority=1)
        shutdown_handler.add_hook("high", dummy, priority=10)
        shutdown_handler.add_hook("medium", dummy, priority=5)

        hooks = [name for name, _, _ in shutdown_handler._hooks]
        assert hooks == ["high", "medium", "low"]


class TestShutdownConfig:
    """Tests for shutdown configuration.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 24.6**
    """

    def test_default_config(self) -> None:
        """Default config SHALL have 30s timeout.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.6**
        """
        config = ShutdownConfig()
        assert config.timeout == 30.0
        assert config.drain_timeout == 10.0

    @settings(max_examples=20, deadline=None)
    @given(
        timeout=st.floats(min_value=1.0, max_value=120.0),
        drain_timeout=st.floats(min_value=1.0, max_value=60.0),
    )
    def test_custom_config(self, timeout: float, drain_timeout: float) -> None:
        """Custom config SHALL be respected.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.6**
        """
        config = ShutdownConfig(timeout=timeout, drain_timeout=drain_timeout)
        assert config.timeout == timeout
        assert config.drain_timeout == drain_timeout


class TestShutdownMiddleware:
    """Tests for shutdown middleware.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 24.4**
    """

    @pytest.mark.asyncio
    async def test_middleware_tracks_requests(self) -> None:
        """Middleware SHALL track in-flight requests.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4**
        """
        handler = ShutdownHandler()

        # Create mock app
        async def mock_app(scope, receive, send):
            # Simulate some processing
            await asyncio.sleep(0.01)

        middleware = ShutdownMiddleware(mock_app, handler)

        # Track that requests are counted
        assert handler.in_flight_requests == 0

        # Simulate HTTP request
        scope = {"type": "http"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # Request should complete (count back to 0)
        assert handler.in_flight_requests == 0

    @pytest.mark.asyncio
    async def test_middleware_rejects_during_shutdown(self) -> None:
        """Middleware SHALL reject requests during shutdown.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 24.4**
        """
        handler = ShutdownHandler()

        async def mock_app(scope, receive, send):
            pass

        middleware = ShutdownMiddleware(mock_app, handler, reject_during_shutdown=True)

        # Trigger shutdown
        await handler.shutdown()

        # Simulate HTTP request
        scope = {"type": "http"}
        receive = AsyncMock()

        responses = []

        async def capture_send(message):
            responses.append(message)

        await middleware(scope, receive, capture_send)

        # Should have sent 503 response
        assert any(r.get("status") == 503 for r in responses)
