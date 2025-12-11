"""Observability configuration.

Contains settings for logging and observability/monitoring.

**Feature: core-config-restructuring-2025**
"""

from core.config.observability.logging import (
    add_request_id,
    add_trace_context,
    clear_request_id,
    configure_logging,
    get_logger,
    get_request_id,
    redact_pii,
    set_request_id,
)
from core.config.observability.observability import ObservabilitySettings

__all__ = [
    "ObservabilitySettings",
    # Logging functions
    "add_request_id",
    "add_trace_context",
    "clear_request_id",
    "configure_logging",
    "get_logger",
    "get_request_id",
    "redact_pii",
    "set_request_id",
]
