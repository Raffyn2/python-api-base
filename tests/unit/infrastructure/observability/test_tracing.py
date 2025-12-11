"""Tests for tracing module.

Tests for TracingConfig and TracingProvider.
"""

from unittest.mock import patch

import pytest

from infrastructure.observability.tracing import TracingConfig, TracingProvider


class TestTracingConfig:
    """Tests for TracingConfig dataclass."""

    def test_default_service_name(self) -> None:
        """Config should have default service_name."""
        config = TracingConfig()
        assert config.service_name == "my_app"

    def test_default_endpoint(self) -> None:
        """Config should have default endpoint."""
        config = TracingConfig()
        assert config.endpoint == "http://localhost:4317"

    def test_default_enabled(self) -> None:
        """Config should be enabled by default."""
        config = TracingConfig()
        assert config.enabled is True

    def test_custom_service_name(self) -> None:
        """Config should accept custom service_name."""
        config = TracingConfig(service_name="my-service")
        assert config.service_name == "my-service"

    def test_custom_endpoint(self) -> None:
        """Config should accept custom endpoint."""
        config = TracingConfig(endpoint="http://otel:4317")
        assert config.endpoint == "http://otel:4317"

    def test_disabled(self) -> None:
        """Config can be disabled."""
        config = TracingConfig(enabled=False)
        assert config.enabled is False

    def test_all_custom_values(self) -> None:
        """Config should accept all custom values."""
        config = TracingConfig(
            service_name="api",
            endpoint="http://collector:4317",
            enabled=False,
        )
        assert config.service_name == "api"
        assert config.endpoint == "http://collector:4317"
        assert config.enabled is False


class TestTracingProvider:
    """Tests for TracingProvider class."""

    def test_init_default_config(self) -> None:
        """Provider should use default config when none provided."""
        provider = TracingProvider()
        assert provider._config.service_name == "my_app"

    def test_init_custom_config(self) -> None:
        """Provider should use provided config."""
        config = TracingConfig(service_name="custom")
        provider = TracingProvider(config)
        assert provider._config.service_name == "custom"

    def test_init_tracer_is_none(self) -> None:
        """Provider should have None tracer initially."""
        provider = TracingProvider()
        assert provider._tracer is None

    def test_setup_when_disabled(self) -> None:
        """Setup should log when tracing is disabled."""
        config = TracingConfig(enabled=False)
        provider = TracingProvider(config)
        with patch("infrastructure.observability.tracing.logger") as mock_logger:
            provider.setup()
            mock_logger.info.assert_called_once_with("Tracing disabled")

    def test_setup_when_enabled(self) -> None:
        """Setup should log service name when enabled."""
        config = TracingConfig(service_name="test-service")
        provider = TracingProvider(config)
        with patch("infrastructure.observability.tracing.logger") as mock_logger:
            provider.setup()
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["service_name"] == "test-service"

    def test_get_tracer_returns_none(self) -> None:
        """get_tracer should return None (no real tracer configured)."""
        provider = TracingProvider()
        assert provider.get_tracer() is None

    def test_create_span_returns_none(self) -> None:
        """create_span should return None (no real tracer)."""
        provider = TracingProvider()
        result = provider.create_span("test-span")
        assert result is None

    def test_create_span_logs_debug(self) -> None:
        """create_span should log span name at debug level."""
        provider = TracingProvider()
        with patch("infrastructure.observability.tracing.logger") as mock_logger:
            result = provider.create_span("my-span")
            assert result is None
            mock_logger.debug.assert_called_once()
            call_kwargs = mock_logger.debug.call_args[1]
            assert call_kwargs["span_name"] == "my-span"

    def test_shutdown_logs_info(self) -> None:
        """shutdown should log info message."""
        provider = TracingProvider()
        with patch("infrastructure.observability.tracing.logger") as mock_logger:
            provider.shutdown()
            mock_logger.info.assert_called_once_with("Shutting down tracing")

    def test_full_lifecycle(self) -> None:
        """Test full provider lifecycle."""
        config = TracingConfig(service_name="lifecycle-test")
        provider = TracingProvider(config)

        with patch("infrastructure.observability.tracing.logger") as mock_logger:
            provider.setup()
            tracer = provider.get_tracer()
            span = provider.create_span("operation")
            provider.shutdown()

            assert tracer is None
            assert span is None
            # Verify setup was called with service_name
            setup_call = mock_logger.info.call_args_list[0]
            assert setup_call[1]["service_name"] == "lifecycle-test"
            # Verify shutdown was called
            shutdown_call = mock_logger.info.call_args_list[1]
            assert shutdown_call[0][0] == "Shutting down tracing"
