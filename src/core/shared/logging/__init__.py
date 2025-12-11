"""Structured logging infrastructure with ECS compatibility.

Provides:
- Structlog configuration with JSON output
- Correlation ID propagation
- PII redaction
- Elasticsearch transport

**Feature: observability-infrastructure**
**Requirement: R1 - Structured Logging Infrastructure**
"""

from core.shared.logging.config import (
    LogLevel,
    configure_logging,
    get_logger,
)
from core.shared.logging.correlation import (
    bind_contextvars,
    clear_contextvars,
    clear_correlation_id,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    unbind_contextvars,
)
from core.shared.logging.redaction import (
    PII_PATTERNS,
    RedactionProcessor,
)

__all__ = [
    "PII_PATTERNS",
    "LogLevel",
    # Redaction
    "RedactionProcessor",
    "bind_contextvars",
    "clear_contextvars",
    "clear_correlation_id",
    # Config
    "configure_logging",
    # Correlation
    "generate_correlation_id",
    "get_correlation_id",
    "get_logger",
    "set_correlation_id",
    "unbind_contextvars",
]
