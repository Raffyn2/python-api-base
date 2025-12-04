"""OpenTelemetry integration for distributed tracing and metrics.

This module provides:
- TracerProvider and MeterProvider initialization
- OTLP exporter configuration
- @traced decorator for custom spans
- OpenTelemetry-compliant type definitions

Feature: file-size-compliance-phase2
Improvement: P1-1 - Added telemetry type definitions
"""

from infrastructure.observability.telemetry.noop import (
    _NoOpCounter,
    _NoOpHistogram,
    _NoOpMeter,
    _NoOpSpan,
    _NoOpTracer,
)
from infrastructure.observability.telemetry.service import (
    P,
    TelemetryProvider,
    _current_span_id,
    _current_trace_id,
    get_current_span_id,
    get_current_trace_id,
    get_telemetry,
    init_telemetry,
    traced,
)
from infrastructure.observability.telemetry.types import (
    AttributePrimitive,
    Attributes,
    AttributeSequence,
    AttributeValue,
)

__all__ = [
    "AttributePrimitive",
    "AttributeSequence",
    "AttributeValue",
    "Attributes",
    "P",
    "TelemetryProvider",
    "_NoOpCounter",
    "_NoOpHistogram",
    "_NoOpMeter",
    "_NoOpSpan",
    "_NoOpTracer",
    "_current_span_id",
    "_current_trace_id",
    "get_current_span_id",
    "get_current_trace_id",
    "get_telemetry",
    "init_telemetry",
    "traced",
]
