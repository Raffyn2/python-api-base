"""Generic resilience patterns with PEP 695 type parameters.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5**
**Refactored: Split into circuit_breaker.py, retry_pattern.py, timeout.py, fallback.py, bulkhead.py**
"""

# Re-export for backward compatibility
from infrastructure.resilience.bulkhead import (
    Bulkhead,
    BulkheadConfig,
    BulkheadRegistry,
    BulkheadRejectedError,
    BulkheadState,
    BulkheadStats,
    bulkhead,
)
from infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from infrastructure.resilience.fallback import Fallback
from infrastructure.resilience.retry_pattern import (
    BackoffStrategy,
    ExponentialBackoff,
    Retry,
    RetryConfig,
)
from infrastructure.resilience.timeout import Timeout, TimeoutConfig

__all__ = [
    "BackoffStrategy",
    "Bulkhead",
    # Bulkhead
    "BulkheadConfig",
    "BulkheadRegistry",
    "BulkheadRejectedError",
    "BulkheadState",
    "BulkheadStats",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    # Circuit Breaker
    "CircuitState",
    "ExponentialBackoff",
    # Fallback
    "Fallback",
    "Retry",
    # Retry
    "RetryConfig",
    "Timeout",
    # Timeout
    "TimeoutConfig",
    "bulkhead",
]
