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
    get_correlation_id,
    set_correlation_id,
)
from core.shared.logging.redaction import (
    PII_PATTERNS,
    RedactionProcessor,
)

__all__ = [
    # Config
    "configure_logging",
    "get_logger",
    "LogLevel",
    # Correlation
    "get_correlation_id",
    "set_correlation_id",
    "bind_contextvars",
    "clear_contextvars",
    # Redaction
    "RedactionProcessor",
    "PII_PATTERNS",
]
