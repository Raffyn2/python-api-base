"""Tests for Prometheus endpoint module.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements R5.4, R5.5 - Metrics Endpoint**
"""

from unittest.mock import MagicMock, patch

import pytest

from infrastructure.prometheus.endpoint import create_metrics_endpoint, setup_prometheus


class TestCreateMetricsEndpoint:
    """Tests for create_metrics_endpoint function."""

    def test_returns_router(self) -> None:
        """Test that function returns an APIRouter."""
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            router = create_metrics_endpoint()
            assert router is not None
            assert hasattr(router, "routes")

    def test_default_path(self) -> None:
        """Test default metrics path."""
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            router = create_metrics_endpoint()
            paths = [route.path for route in router.routes]
            assert "/metrics" in paths

    def test_custom_path(self) -> None:
        """Test custom metrics path."""
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            router = create_metrics_endpoint(path="/custom-metrics")
            paths = [route.path for route in router.routes]
            assert "/custom-metrics" in paths

    def test_custom_registry(self) -> None:
        """Test with custom registry."""
        custom_registry = MagicMock()
        router = create_metrics_endpoint(registry=custom_registry)
        assert router is not None

    def test_default_tags(self) -> None:
        """Test default tags."""
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            router = create_metrics_endpoint()
            assert "Metrics" in router.tags

    def test_custom_tags(self) -> None:
        """Test custom tags."""
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            router = create_metrics_endpoint(tags=["Custom"])
            assert "Custom" in router.tags


class TestSetupPrometheus:
    """Tests for setup_prometheus function."""

    def test_adds_middleware(self) -> None:
        """Test that middleware is added to app."""
        app = MagicMock()
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            setup_prometheus(app)
            app.add_middleware.assert_called_once()

    def test_includes_router(self) -> None:
        """Test that router is included in app."""
        app = MagicMock()
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            setup_prometheus(app)
            app.include_router.assert_called_once()

    def test_custom_endpoint(self) -> None:
        """Test with custom endpoint path."""
        app = MagicMock()
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            setup_prometheus(app, endpoint="/custom-metrics")
            app.include_router.assert_called_once()

    def test_custom_skip_paths(self) -> None:
        """Test with custom skip paths."""
        app = MagicMock()
        with patch("infrastructure.prometheus.endpoint.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            setup_prometheus(app, skip_paths=["/custom"])
            app.add_middleware.assert_called_once()

    def test_custom_registry(self) -> None:
        """Test with custom registry."""
        app = MagicMock()
        custom_registry = MagicMock()
        setup_prometheus(app, registry=custom_registry)
        app.add_middleware.assert_called_once()
        app.include_router.assert_called_once()
