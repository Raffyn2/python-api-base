"""Trace context integration for structured logging.

This module provides a structlog processor that adds OpenTelemetry trace
context (trace_id, span_id) to all log entries.

**Feature: dapr-sidecar-integration**
**Requirement: R10.4 - Log Correlation with Trace Context**

Example:
    >>> from core.shared.logging import configure_logging
    >>> from core.shared.logging.trace_context import add_trace_context
    >>> configure_logging(extra_processors=[add_trace_context])
"""

from __future__ import annotations

import logging
from typing import Any


def add_trace_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that adds OpenTelemetry trace context to logs.

    Extracts trace_id and span_id from the current OpenTelemetry span
    and adds them to the log event dictionary.

    Args:
        logger: The logger instance
        method_name: The logging method name (info, debug, etc.)
        event_dict: The event dictionary to process

    Returns:
        The event dictionary with trace context added
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.is_valid:
            event_dict["trace_id"] = format(span_context.trace_id, "032x")
            event_dict["span_id"] = format(span_context.span_id, "016x")
            event_dict["trace_flags"] = span_context.trace_flags

            if span.is_recording():
                event_dict["trace_sampled"] = True
    except ImportError:
        pass
    except Exception:
        pass

    return event_dict


def add_dapr_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that adds Dapr-specific context to logs.

    Adds Dapr app ID and other Dapr-related context to log entries.

    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The event dictionary to process

    Returns:
        The event dictionary with Dapr context added
    """
    try:
        from core.config.dapr import get_dapr_settings

        settings = get_dapr_settings()
        if settings.enabled:
            event_dict["dapr_app_id"] = settings.app_id
    except ImportError:
        pass
    except Exception:
        pass

    return event_dict


def get_trace_context_processors() -> list:
    """Get the list of trace context processors for structlog.

    Returns:
        List of processors to add trace context to logs
    """
    return [add_trace_context, add_dapr_context]
