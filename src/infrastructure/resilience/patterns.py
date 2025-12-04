"""Generic resilience patterns with PEP 695 type parameters.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5**
**Refactored: Split into circuit_breaker.py, retry_pattern.py, timeout.py, fallback.py, bulkhead.py**
"""

# Re-export for backward compatibility
from .bulkhead import (
    Bulkhead,
    BulkheadConfig,
    BulkheadRegistry,
    BulkheadRejectedError,
    BulkheadState,
    BulkheadStats,
    bulkhead,
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from .fallback import Fallback
from .retry_pattern import BackoffStrategy, ExponentialBackoff, Retry, RetryConfig
from .timeout import Timeout, TimeoutConfig

__all__ = [
    # Circuit Breaker
    "CircuitState",
    "CircuitBreakerConfig",
    "CircuitBreaker",
    # Retry
    "RetryConfig",
    "BackoffStrategy",
    "ExponentialBackoff",
    "Retry",
    # Timeout
    "TimeoutConfig",
    "Timeout",
    # Fallback
    "Fallback",
    # Bulkhead
    "BulkheadConfig",
    "Bulkhead",
    "BulkheadRegistry",
    "BulkheadRejectedError",
    "BulkheadState",
    "BulkheadStats",
    "bulkhead",
]
