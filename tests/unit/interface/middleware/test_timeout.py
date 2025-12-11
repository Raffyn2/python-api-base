"""Unit tests for timeout middleware.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 6.4 (Timeout handling)**
"""

import asyncio
import importlib.util

# Import directly to avoid circular import issues
import sys
from datetime import timedelta

import pytest

# Load the timeout module directly
spec = importlib.util.spec_from_file_location("timeout_module", "src/interface/middleware/request/timeout.py")
timeout_module = importlib.util.module_from_spec(spec)
sys.modules["timeout_module"] = timeout_module
spec.loader.exec_module(timeout_module)

TimeoutConfig = timeout_module.TimeoutConfig
TimeoutMiddleware = timeout_module.TimeoutMiddleware
TimeoutAction = timeout_module.TimeoutAction
TimeoutResult = timeout_module.TimeoutResult
TimeoutError = timeout_module.TimeoutError
TimeoutConfigBuilder = timeout_module.TimeoutConfigBuilder
timeout_decorator = timeout_module.timeout_decorator
create_timeout_middleware = timeout_module.create_timeout_middleware


class TestTimeoutConfig:
    """Tests for TimeoutConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = TimeoutConfig()

        assert config.default_timeout == timedelta(seconds=30)
        assert config.endpoint_timeouts == {}
        assert config.action == TimeoutAction.RAISE
        assert config.default_response is None
        assert config.log_timeouts is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = TimeoutConfig(
            default_timeout=timedelta(seconds=60),
            endpoint_timeouts={"/slow": timedelta(seconds=120)},
            action=TimeoutAction.CANCEL,
            log_timeouts=False,
        )

        assert config.default_timeout == timedelta(seconds=60)
        assert config.endpoint_timeouts == {"/slow": timedelta(seconds=120)}
        assert config.action == TimeoutAction.CANCEL
        assert config.log_timeouts is False


class TestTimeoutResult:
    """Tests for TimeoutResult dataclass."""

    def test_ok_result(self) -> None:
        """Test successful result creation."""
        result = TimeoutResult.ok(response="success", elapsed=1.5)

        assert result.success is True
        assert result.response == "success"
        assert result.elapsed == 1.5
        assert result.timed_out is False
        assert result.error is None

    def test_timeout_result(self) -> None:
        """Test timeout result creation."""
        result = TimeoutResult.timeout(elapsed=30.0)

        assert result.success is False
        assert result.timed_out is True
        assert result.elapsed == 30.0
        assert result.response is None

    def test_failed_result(self) -> None:
        """Test failed result creation."""
        error = ValueError("Test error")
        result = TimeoutResult.failed(error=error, elapsed=2.0)

        assert result.success is False
        assert result.error == error
        assert result.elapsed == 2.0
        assert result.timed_out is False


class TestTimeoutMiddleware:
    """Tests for TimeoutMiddleware."""

    def test_get_timeout_default(self) -> None:
        """Test getting default timeout."""
        config = TimeoutConfig(default_timeout=timedelta(seconds=30))
        middleware = TimeoutMiddleware(config=config)

        assert middleware.get_timeout("/any/endpoint") == 30.0

    def test_get_timeout_endpoint_specific(self) -> None:
        """Test getting endpoint-specific timeout."""
        config = TimeoutConfig(
            default_timeout=timedelta(seconds=30),
            endpoint_timeouts={"/slow": timedelta(seconds=120)},
        )
        middleware = TimeoutMiddleware(config=config)

        assert middleware.get_timeout("/slow") == 120.0
        assert middleware.get_timeout("/fast") == 30.0

    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        """Test successful execution within timeout."""
        config = TimeoutConfig(default_timeout=timedelta(seconds=5))
        middleware = TimeoutMiddleware(config=config)

        async def fast_handler():
            return "success"

        result = await middleware.execute(fast_handler, endpoint="/test")

        assert result.success is True
        assert result.response == "success"
        assert result.timed_out is False

    @pytest.mark.asyncio
    async def test_execute_timeout_raises(self) -> None:
        """Test that timeout raises TimeoutError when action is RAISE."""
        config = TimeoutConfig(
            default_timeout=timedelta(milliseconds=10),
            action=TimeoutAction.RAISE,
        )
        middleware = TimeoutMiddleware(config=config)

        async def slow_handler():
            await asyncio.sleep(1)
            return "never"

        with pytest.raises(TimeoutError) as exc_info:
            await middleware.execute(slow_handler, endpoint="/slow")

        assert exc_info.value.endpoint == "/slow"

    @pytest.mark.asyncio
    async def test_execute_timeout_returns_default(self) -> None:
        """Test that timeout returns default when action is RETURN_DEFAULT."""
        config = TimeoutConfig(
            default_timeout=timedelta(milliseconds=10),
            action=TimeoutAction.RETURN_DEFAULT,
            default_response="default_value",
        )
        middleware = TimeoutMiddleware(config=config)

        async def slow_handler():
            await asyncio.sleep(1)
            return "never"

        result = await middleware.execute(slow_handler, endpoint="/slow")

        assert result.timed_out is True
        assert result.response == "default_value"

    @pytest.mark.asyncio
    async def test_execute_timeout_cancel(self) -> None:
        """Test that timeout cancels when action is CANCEL."""
        config = TimeoutConfig(
            default_timeout=timedelta(milliseconds=10),
            action=TimeoutAction.CANCEL,
        )
        middleware = TimeoutMiddleware(config=config)

        async def slow_handler():
            await asyncio.sleep(1)
            return "never"

        result = await middleware.execute(slow_handler, endpoint="/slow")

        assert result.success is False
        assert result.timed_out is True

    @pytest.mark.asyncio
    async def test_execute_handler_error(self) -> None:
        """Test handling of handler errors."""
        config = TimeoutConfig(default_timeout=timedelta(seconds=5))
        middleware = TimeoutMiddleware(config=config)

        async def error_handler():
            raise ValueError("Handler error")

        result = await middleware.execute(error_handler, endpoint="/error")

        assert result.success is False
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Handler error"


class TestTimeoutConfigBuilder:
    """Tests for TimeoutConfigBuilder."""

    def test_build_default(self) -> None:
        """Test building config with defaults."""
        config = TimeoutConfigBuilder().build()

        assert config.default_timeout == timedelta(seconds=30)
        assert config.action == TimeoutAction.RAISE

    def test_build_with_custom_timeout(self) -> None:
        """Test building config with custom timeout."""
        config = TimeoutConfigBuilder().with_default_timeout_seconds(60).build()

        assert config.default_timeout == timedelta(seconds=60)

    def test_build_with_endpoint_timeouts(self) -> None:
        """Test building config with endpoint-specific timeouts."""
        config = (
            TimeoutConfigBuilder()
            .for_endpoint_seconds("/slow", 120)
            .for_endpoint("/upload", timedelta(minutes=5))
            .build()
        )

        assert config.endpoint_timeouts["/slow"] == timedelta(seconds=120)
        assert config.endpoint_timeouts["/upload"] == timedelta(minutes=5)

    def test_build_with_action(self) -> None:
        """Test building config with custom action."""
        config = TimeoutConfigBuilder().with_action(TimeoutAction.CANCEL).build()

        assert config.action == TimeoutAction.CANCEL

    def test_fluent_interface(self) -> None:
        """Test fluent builder interface."""
        config = (
            TimeoutConfigBuilder()
            .with_default_timeout_seconds(45)
            .for_endpoint_seconds("/api/slow", 90)
            .with_action(TimeoutAction.RETURN_DEFAULT)
            .with_default_response({"error": "timeout"})
            .with_logging(False)
            .build()
        )

        assert config.default_timeout == timedelta(seconds=45)
        assert config.endpoint_timeouts["/api/slow"] == timedelta(seconds=90)
        assert config.action == TimeoutAction.RETURN_DEFAULT
        assert config.default_response == {"error": "timeout"}
        assert config.log_timeouts is False


class TestTimeoutDecorator:
    """Tests for timeout_decorator."""

    @pytest.mark.asyncio
    async def test_decorator_success(self) -> None:
        """Test decorator with successful execution."""

        @timeout_decorator(timeout_seconds=5)
        async def fast_function():
            return "success"

        result = await fast_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorator_timeout(self) -> None:
        """Test decorator raises on timeout."""

        @timeout_decorator(timeout_seconds=0.01)
        async def slow_function():
            await asyncio.sleep(1)
            return "never"

        with pytest.raises(TimeoutError):
            await slow_function()


class TestCreateTimeoutMiddleware:
    """Tests for create_timeout_middleware factory."""

    def test_creates_middleware_with_defaults(self) -> None:
        """Test factory creates middleware with defaults."""
        middleware = create_timeout_middleware()

        assert middleware._config.default_timeout == timedelta(seconds=30)

    def test_creates_middleware_with_config(self) -> None:
        """Test factory creates middleware with custom config."""
        config = TimeoutConfig(default_timeout=timedelta(seconds=60))
        middleware = create_timeout_middleware(config=config)

        assert middleware._config.default_timeout == timedelta(seconds=60)
