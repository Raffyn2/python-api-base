"""Unit tests for resilience middleware.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 16.1 (Circuit Breaker)**
"""

import importlib.util

# Import directly to avoid circular import issues
import sys
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Load the resilience module directly
spec = importlib.util.spec_from_file_location("resilience_module", "src/interface/middleware/production/resilience.py")
resilience_module = importlib.util.module_from_spec(spec)
sys.modules["resilience_module"] = resilience_module
spec.loader.exec_module(resilience_module)

ResilienceConfig = resilience_module.ResilienceConfig
ResilienceMiddleware = resilience_module.ResilienceMiddleware


class TestResilienceConfig:
    """Tests for ResilienceConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ResilienceConfig()

        assert config.failure_threshold == 5
        assert config.timeout == timedelta(seconds=30)
        assert config.enabled is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = ResilienceConfig(
            failure_threshold=10,
            timeout=timedelta(seconds=60),
            enabled=False,
        )

        assert config.failure_threshold == 10
        assert config.timeout == timedelta(seconds=60)
        assert config.enabled is False


class TestResilienceMiddlewareInit:
    """Tests for ResilienceMiddleware initialization."""

    def test_creates_circuit_breaker(self) -> None:
        """Test that circuit breaker is created on init."""
        app = MagicMock()
        config = ResilienceConfig(failure_threshold=3)

        middleware = ResilienceMiddleware(app, config=config)

        assert middleware._circuit is not None
        assert middleware._config.failure_threshold == 3

    def test_uses_default_config(self) -> None:
        """Test that default config is used when not provided."""
        app = MagicMock()

        middleware = ResilienceMiddleware(app, config=None)

        assert middleware._config.failure_threshold == 5
        assert middleware._config.enabled is True


class TestCircuitBreakerBehavior:
    """Tests for circuit breaker behavior."""

    def test_circuit_opens_after_threshold(self) -> None:
        """Test that circuit opens after failure threshold is reached."""
        from infrastructure.resilience import CircuitBreaker, CircuitBreakerConfig

        # Create circuit breaker with low threshold
        circuit = CircuitBreaker(
            "test",
            CircuitBreakerConfig(failure_threshold=2, timeout=timedelta(seconds=30)),
        )

        # Record failures (using internal methods)
        circuit._record_failure()
        assert circuit._can_execute() is True

        circuit._record_failure()
        # After threshold, circuit should be open
        assert circuit._can_execute() is False

    def test_circuit_allows_after_timeout(self) -> None:
        """Test that circuit allows requests after timeout (half-open)."""
        from infrastructure.resilience import CircuitBreaker, CircuitBreakerConfig

        # Create circuit breaker with very short timeout
        circuit = CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=1,
                timeout=timedelta(milliseconds=1),
            ),
        )

        # Open the circuit
        circuit._record_failure()
        assert circuit._can_execute() is False

        # Wait for timeout
        import time

        time.sleep(0.01)

        # Circuit should be half-open now
        assert circuit._can_execute() is True

    def test_success_closes_circuit(self) -> None:
        """Test that success closes the circuit."""
        from infrastructure.resilience import CircuitBreaker, CircuitBreakerConfig

        circuit = CircuitBreaker(
            "test",
            CircuitBreakerConfig(
                failure_threshold=1,
                success_threshold=1,
                timeout=timedelta(milliseconds=1),
            ),
        )

        # Open the circuit
        circuit._record_failure()

        # Wait for half-open
        import time

        time.sleep(0.01)

        # Record success
        circuit._record_success()

        # Circuit should be closed
        assert circuit._can_execute() is True


class TestMiddlewareDispatch:
    """Tests for middleware dispatch behavior."""

    @pytest.mark.asyncio
    async def test_bypasses_when_disabled(self) -> None:
        """Test that middleware is bypassed when disabled."""
        app = MagicMock()
        config = ResilienceConfig(enabled=False)
        middleware = ResilienceMiddleware(app, config=config)

        request = MagicMock()
        request.headers = {}
        expected_response = MagicMock()
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_records_success_on_2xx(self) -> None:
        """Test that success is recorded for 2xx responses."""
        app = MagicMock()
        config = ResilienceConfig()
        middleware = ResilienceMiddleware(app, config=config)

        request = MagicMock()
        request.headers = {}
        response = MagicMock()
        response.status_code = 200
        call_next = AsyncMock(return_value=response)

        with patch.object(middleware._circuit, "_record_success") as mock_success:
            await middleware.dispatch(request, call_next)
            mock_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_failure_on_5xx(self) -> None:
        """Test that failure is recorded for 5xx responses."""
        app = MagicMock()
        config = ResilienceConfig()
        middleware = ResilienceMiddleware(app, config=config)

        request = MagicMock()
        request.headers = {}
        response = MagicMock()
        response.status_code = 500
        call_next = AsyncMock(return_value=response)

        with patch.object(middleware._circuit, "_record_failure") as mock_failure:
            await middleware.dispatch(request, call_next)
            mock_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_503_when_circuit_open(self) -> None:
        """Test that 503 is returned when circuit is open."""
        app = MagicMock()
        config = ResilienceConfig()
        middleware = ResilienceMiddleware(app, config=config)

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/test"
        request.headers = {}
        call_next = AsyncMock()

        with patch.object(middleware._circuit, "_can_execute", return_value=False):
            with patch.object(resilience_module, "logger"):
                response = await middleware.dispatch(request, call_next)

        assert response.status_code == 503
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_records_failure_on_exception(self) -> None:
        """Test that failure is recorded when exception is raised."""
        app = MagicMock()
        config = ResilienceConfig()
        middleware = ResilienceMiddleware(app, config=config)

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/test"
        request.headers = {}
        call_next = AsyncMock(side_effect=ValueError("Test error"))

        with patch.object(middleware._circuit, "_record_failure") as mock_failure:
            with patch.object(resilience_module, "logger"), pytest.raises(ValueError):
                await middleware.dispatch(request, call_next)

            mock_failure.assert_called_once()


class TestLogging:
    """Tests for logging behavior."""

    @pytest.mark.asyncio
    async def test_logs_circuit_open_with_correlation_id(self) -> None:
        """Test that circuit open is logged with correlation ID."""
        app = MagicMock()
        config = ResilienceConfig()
        middleware = ResilienceMiddleware(app, config=config)

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/test"
        request.headers = {"X-Request-ID": "test-correlation-123"}
        call_next = AsyncMock()

        with patch.object(middleware._circuit, "_can_execute", return_value=False):
            with patch.object(resilience_module, "logger") as mock_logger:
                await middleware.dispatch(request, call_next)

                mock_logger.warning.assert_called_once()
                call_kwargs = mock_logger.warning.call_args[1]
                assert call_kwargs["correlation_id"] == "test-correlation-123"

    @pytest.mark.asyncio
    async def test_logs_request_failure_with_correlation_id(self) -> None:
        """Test that request failures are logged with correlation ID."""
        app = MagicMock()
        config = ResilienceConfig()
        middleware = ResilienceMiddleware(app, config=config)

        request = MagicMock()
        request.url = MagicMock()
        request.url.path = "/test"
        request.headers = {"X-Correlation-ID": "corr-456"}
        call_next = AsyncMock(side_effect=ValueError("Test error"))

        with patch.object(resilience_module, "logger") as mock_logger:
            with pytest.raises(ValueError):
                await middleware.dispatch(request, call_next)

            # The code uses logger.exception, not logger.error
            mock_logger.exception.assert_called_once()
            call_kwargs = mock_logger.exception.call_args[1]
            assert call_kwargs["correlation_id"] == "corr-456"
