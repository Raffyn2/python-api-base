"""Observability middleware for command bus.

Provides:
- LoggingMiddleware: Structured logging with correlation IDs
- IdempotencyMiddleware: Prevents duplicate command execution
- MetricsMiddleware: Command execution metrics and performance tracking

**Feature: enterprise-features-2025**
**Validates: Requirements 12.1, 12.2, 12.3, 12.4**
**Refactored: Split into logging_middleware.py, idempotency_middleware.py, metrics_middleware.py**
"""

# Re-export for backward compatibility
from .idempotency_middleware import (
    IdempotencyCache,
    IdempotencyConfig,
    IdempotencyMiddleware,
    InMemoryIdempotencyCache,
)
from .logging_middleware import (
    LoggingConfig,
    LoggingMiddleware,
    generate_request_id,
    get_request_id,
    request_id_var,
    set_request_id,
)
from .metrics_middleware import (
    InMemoryMetricsCollector,
    MetricsCollector,
    MetricsConfig,
    MetricsMiddleware,
)

__all__ = [
    # Logging
    "LoggingConfig",
    "LoggingMiddleware",
    "request_id_var",
    "get_request_id",
    "set_request_id",
    "generate_request_id",
    # Idempotency
    "IdempotencyCache",
    "InMemoryIdempotencyCache",
    "IdempotencyConfig",
    "IdempotencyMiddleware",
    # Metrics
    "MetricsCollector",
    "InMemoryMetricsCollector",
    "MetricsConfig",
    "MetricsMiddleware",
]
