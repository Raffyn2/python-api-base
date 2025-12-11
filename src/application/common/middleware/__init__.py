"""Middleware components for command/query pipelines.

Organized into subpackages by responsibility:
- cache/: Query caching and cache invalidation
- resilience/: Retry, circuit breaker, and resilience patterns
- observability/: Logging, metrics, and monitoring
- operations/: Transaction and idempotency management
- validation/: Command validation

Provides cross-cutting concerns:
- Transaction: Unit of work management
- Validation: Command validation
- Resilience: Retry, circuit breaker
- Observability: Logging, metrics
- Caching: Query result caching
- Idempotency: Duplicate request handling

**Architecture: Middleware Pattern**
**Feature: architecture-restructuring-2025**
"""

from application.common.middleware.cache import (
    CacheInvalidationMiddleware,
    CacheInvalidationStrategy,
    CompositeCacheInvalidationStrategy,
    InMemoryQueryCache,
    InvalidationRule,
    ItemCacheInvalidationStrategy,
    QueryCache,
    QueryCacheConfig,
    QueryCacheMiddleware,
    UserCacheInvalidationStrategy,
    create_entity_specific_pattern,
    create_query_type_pattern,
)
from application.common.middleware.observability import (
    InMemoryMetricsCollector,
    LoggingConfig,
    LoggingMiddleware,
    MetricsCollector,
    MetricsConfig,
    MetricsMiddleware,
    generate_request_id,
    get_request_id,
    request_id_var,
    set_request_id,
)
from application.common.middleware.operations import (
    DEFAULT_TRANSACTION_CONFIG,
    IdempotencyCache,
    IdempotencyConfig,
    IdempotencyMiddleware,
    InMemoryIdempotencyCache,
    Middleware,
    TransactionConfig,
    TransactionMiddleware,
)
from application.common.middleware.resilience import (
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CircuitBreakerOpenError,
    CircuitBreakerStats,
    CircuitState,
    ResilienceMiddleware,
    RetryConfig,
    RetryExhaustedError,
    RetryMiddleware,
)
from application.common.middleware.validation import (
    CompositeValidator,
    RangeValidator,
    RequiredFieldValidator,
    StringLengthValidator,
    ValidationError,
    ValidationMiddleware,
    Validator,
)

__all__ = [
    # Operations
    "DEFAULT_TRANSACTION_CONFIG",
    # Cache
    "CacheInvalidationMiddleware",
    "CacheInvalidationStrategy",
    # Resilience
    "CircuitBreakerConfig",
    "CircuitBreakerMiddleware",
    "CircuitBreakerOpenError",
    "CircuitBreakerStats",
    "CircuitState",
    "CompositeCacheInvalidationStrategy",
    # Validation
    "CompositeValidator",
    "IdempotencyCache",
    "IdempotencyConfig",
    "IdempotencyMiddleware",
    "InMemoryIdempotencyCache",
    # Observability
    "InMemoryMetricsCollector",
    "InMemoryQueryCache",
    "InvalidationRule",
    "ItemCacheInvalidationStrategy",
    "LoggingConfig",
    "LoggingMiddleware",
    "MetricsCollector",
    "MetricsConfig",
    "MetricsMiddleware",
    "Middleware",
    "QueryCache",
    "QueryCacheConfig",
    "QueryCacheMiddleware",
    "RangeValidator",
    "RequiredFieldValidator",
    "ResilienceMiddleware",
    "RetryConfig",
    "RetryExhaustedError",
    "RetryMiddleware",
    "StringLengthValidator",
    "TransactionConfig",
    "TransactionMiddleware",
    "UserCacheInvalidationStrategy",
    "ValidationError",
    "ValidationMiddleware",
    "Validator",
    "create_entity_specific_pattern",
    "create_query_type_pattern",
    "generate_request_id",
    "get_request_id",
    "request_id_var",
    "set_request_id",
]
