"""Middleware components for command/query pipelines.

Provides cross-cutting concerns:
- Transaction: Unit of work management
- Validation: Command validation
- Resilience: Retry, circuit breaker
- Observability: Logging, idempotency, metrics
- Caching: Query result caching

**Architecture: Middleware Pattern**
"""

from application.common.middleware.cache_invalidation import (
    CacheInvalidationMiddleware,
    CacheInvalidationStrategy,
    CompositeCacheInvalidationStrategy,
    InvalidationRule,
    ItemCacheInvalidationStrategy,
    UserCacheInvalidationStrategy,
    create_entity_specific_pattern,
    create_query_type_pattern,
)
from application.common.middleware.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CircuitBreakerOpenError,
    CircuitState,
)
from application.common.middleware.observability import (
    IdempotencyCache,
    IdempotencyConfig,
    IdempotencyMiddleware,
    InMemoryIdempotencyCache,
    InMemoryMetricsCollector,
    LoggingConfig,
    LoggingMiddleware,
    MetricsCollector,
    MetricsConfig,
    MetricsMiddleware,
    generate_request_id,
    get_request_id,
    set_request_id,
)
from application.common.middleware.query_cache import (
    InMemoryQueryCache,
    QueryCache,
    QueryCacheConfig,
    QueryCacheMiddleware,
)
from application.common.middleware.resilience import ResilienceMiddleware
from application.common.middleware.retry import (
    RetryConfig,
    RetryExhaustedError,
    RetryMiddleware,
)
from application.common.middleware.transaction import (
    DEFAULT_TRANSACTION_CONFIG,
    Middleware,
    TransactionConfig,
    TransactionMiddleware,
)
from application.common.middleware.validation import (
    CompositeValidator,
    RangeValidator,
    RequiredFieldValidator,
    StringLengthValidator,
    ValidationMiddleware,
    Validator,
)

__all__ = [
    "DEFAULT_TRANSACTION_CONFIG",
    "CacheInvalidationMiddleware",
    # Cache Invalidation
    "CacheInvalidationStrategy",
    "CircuitBreakerConfig",
    "CircuitBreakerMiddleware",
    "CircuitBreakerOpenError",
    "CircuitState",
    "CompositeCacheInvalidationStrategy",
    "CompositeValidator",
    "IdempotencyCache",
    "IdempotencyConfig",
    "IdempotencyMiddleware",
    "InMemoryIdempotencyCache",
    "InMemoryMetricsCollector",
    "InMemoryQueryCache",
    "InvalidationRule",
    "ItemCacheInvalidationStrategy",
    "LoggingConfig",
    # Observability
    "LoggingMiddleware",
    "MetricsCollector",
    "MetricsConfig",
    "MetricsMiddleware",
    # Transaction
    "Middleware",
    "QueryCache",
    "QueryCacheConfig",
    # Query Caching
    "QueryCacheMiddleware",
    "RangeValidator",
    "RequiredFieldValidator",
    "ResilienceMiddleware",
    "RetryConfig",
    "RetryExhaustedError",
    # Resilience
    "RetryMiddleware",
    "StringLengthValidator",
    "TransactionConfig",
    "TransactionMiddleware",
    "UserCacheInvalidationStrategy",
    # Validation
    "ValidationMiddleware",
    "Validator",
    "create_entity_specific_pattern",
    "create_query_type_pattern",
    "generate_request_id",
    "get_request_id",
    "set_request_id",
]
