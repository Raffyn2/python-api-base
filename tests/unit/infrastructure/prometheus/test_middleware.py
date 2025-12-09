"""Tests for Prometheus middleware module.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements R5.3 - HTTP Metrics Middleware**
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.prometheus.middleware import PrometheusMiddleware


class TestPrometheusMiddlewareInit:
    """Tests for PrometheusMiddleware initialization."""

    def test_default_skip_paths(self) -> None:
        """Test default skip paths."""
        app = MagicMock()
        with patch("infrastructure.prometheus.middleware.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            middleware = PrometheusMiddleware(app)
            assert "/metrics" in middleware._skip_paths
            assert "/health" in middleware._skip_paths
            assert "/ready" in middleware._skip_paths

    def test_custom_skip_paths(self) -> None:
        """Test custom skip paths."""
        app = MagicMock()
        with patch("infrastructure.prometheus.middleware.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            middleware = PrometheusMiddleware(app, skip_paths=["/custom"])
            assert "/custom" in middleware._skip_paths

    def test_custom_registry(self) -> None:
        """Test custom registry."""
        app = MagicMock()
        custom_registry = MagicMock()
        middleware = PrometheusMiddleware(app, registry=custom_registry)
        assert middleware._registry is custom_registry

    def test_creates_metrics(self) -> None:
        """Test that metrics are created on init."""
        app = MagicMock()
        mock_registry = MagicMock()
        middleware = PrometheusMiddleware(app, registry=mock_registry)
        mock_registry.counter.assert_called_once()
        mock_registry.histogram.assert_called_once()
        mock_registry.gauge.assert_called_once()


class TestPrometheusMiddlewareGetEndpoint:
    """Tests for _get_endpoint method."""

    def test_get_endpoint_from_route(self) -> None:
        """Test getting endpoint from route pattern."""
        app = MagicMock()
        mock_registry = MagicMock()
        middleware = PrometheusMiddleware(app, registry=mock_registry)

        request = MagicMock()
        request.scope = {"route": MagicMock(path="/api/users/{id}")}
        assert middleware._get_endpoint(request) == "/api/users/{id}"

    def test_get_endpoint_from_url(self) -> None:
        """Test getting endpoint from URL path."""
        app = MagicMock()
        mock_registry = MagicMock()
        middleware = PrometheusMiddleware(app, registry=mock_registry)

        request = MagicMock()
        request.scope = {}
        request.url.path = "/api/users/123"
        assert middleware._get_endpoint(request) == "/api/users/123"

    def test_get_endpoint_no_route_path(self) -> None:
        """Test getting endpoint when route has no path attribute."""
        app = MagicMock()
        mock_registry = MagicMock()
        middleware = PrometheusMiddleware(app, registry=mock_registry)

        request = MagicMock()
        route = MagicMock(spec=[])  # No path attribute
        request.scope = {"route": route}
        request.url.path = "/api/users"
        assert middleware._get_endpoint(request) == "/api/users"


class TestPrometheusMiddlewareDispatch:
    """Tests for dispatch method."""

    @pytest.mark.asyncio
    async def test_dispatch_skip_metrics_path(self) -> None:
        """Test dispatch skips metrics path."""
        app = MagicMock()
        mock_registry = MagicMock()
        middleware = PrometheusMiddleware(app, registry=mock_registry)

        request = MagicMock()
        request.url.path = "/metrics"

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_skip_health_path(self) -> None:
        """Test dispatch skips health path."""
        app = MagicMock()
        mock_registry = MagicMock()
        middleware = PrometheusMiddleware(app, registry=mock_registry)

        request = MagicMock()
        request.url.path = "/health"

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_records_metrics(self) -> None:
        """Test dispatch records metrics for normal request."""
        app = MagicMock()
        mock_registry = MagicMock()
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_gauge = MagicMock()
        mock_registry.counter.return_value = mock_counter
        mock_registry.histogram.return_value = mock_histogram
        mock_registry.gauge.return_value = mock_gauge

        middleware = PrometheusMiddleware(app, registry=mock_registry)

        request = MagicMock()
        request.url.path = "/api/users"
        request.method = "GET"
        request.scope = {}

        response = MagicMock()
        response.status_code = 200
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        assert result is response
        mock_gauge.labels.assert_called()
        mock_histogram.labels.assert_called()
        mock_counter.labels.assert_called()

    @pytest.mark.asyncio
    async def test_dispatch_handles_exception(self) -> None:
        """Test dispatch handles exception and records 500 status."""
        app = MagicMock()
        mock_registry = MagicMock()
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        mock_gauge = MagicMock()
        mock_registry.counter.return_value = mock_counter
        mock_registry.histogram.return_value = mock_histogram
        mock_registry.gauge.return_value = mock_gauge

        middleware = PrometheusMiddleware(app, registry=mock_registry)

        request = MagicMock()
        request.url.path = "/api/users"
        request.method = "GET"
        request.scope = {}

        call_next = AsyncMock(side_effect=ValueError("test error"))

        with pytest.raises(ValueError):
            await middleware.dispatch(request, call_next)

        # Metrics should still be recorded
        mock_gauge.labels.assert_called()
        mock_counter.labels.assert_called()
