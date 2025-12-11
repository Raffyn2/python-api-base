"""Resilience middleware for fault tolerance.

Provides circuit breaker, retry, and resilience patterns for handling failures.

**Feature: application-layer-improvements-2025**

Note: This is the CQRS/Application layer resilience for CommandBus.
For HTTP/Infrastructure layer, see: src/infrastructure/resilience/
Architecture decision documented in: docs/architecture/adr/ADR-003-resilience-layers.md
"""

from application.common.middleware.resilience.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CircuitBreakerOpenError,
    CircuitBreakerStats,
    CircuitState,
)
from application.common.middleware.resilience.resilience import (
    ResilienceMiddleware,
)
from application.common.middleware.resilience.retry import (
    RetryConfig,
    RetryExhaustedError,
    RetryMiddleware,
)

__all__ = [
    # Circuit Breaker
    "CircuitBreakerConfig",
    "CircuitBreakerMiddleware",
    "CircuitBreakerOpenError",
    "CircuitBreakerStats",
    "CircuitState",
    # Combined
    "ResilienceMiddleware",
    # Retry
    "RetryConfig",
    "RetryExhaustedError",
    "RetryMiddleware",
]
