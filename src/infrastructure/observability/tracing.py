"""OpenTelemetry tracing setup.

.. deprecated:: 2025.1
    This module is deprecated. Use `infrastructure.observability.telemetry` instead,
    which provides a more complete implementation with:
    - TelemetryProvider with tracer and meter
    - @traced decorator
    - Context variable management for trace/span IDs
    - NoOp implementations for graceful degradation

This module will be removed in a future version.
"""

import warnings
from dataclasses import dataclass
from typing import Any

import structlog

warnings.warn(
    "infrastructure.observability.tracing is deprecated. Use infrastructure.observability.telemetry instead.",
    DeprecationWarning,
    stacklevel=2,
)

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class TracingConfig:
    """Configuration for OpenTelemetry tracing."""

    service_name: str = "my_app"
    endpoint: str = "http://localhost:4317"
    enabled: bool = True


class TracingProvider:
    """Provider for OpenTelemetry tracing functionality."""

    def __init__(self, config: TracingConfig | None = None) -> None:
        self._config = config or TracingConfig()
        self._tracer = None

    def setup(self) -> None:
        if not self._config.enabled:
            logger.info("Tracing disabled")
            return
        logger.info(
            "Setting up tracing",
            service_name=self._config.service_name,
            operation="TRACE_SETUP",
        )

    def get_tracer(self) -> Any:
        return self._tracer

    def create_span(self, name: str) -> Any:
        logger.debug(
            "Creating span",
            span_name=name,
            operation="TRACE_SPAN_CREATE",
        )
        return None

    def shutdown(self) -> None:
        logger.info("Shutting down tracing")
