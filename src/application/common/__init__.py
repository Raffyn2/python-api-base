"""Shared application infrastructure.

Provides common components for all bounded contexts:
- DTOs/Errors/Mappers/UseCases: Application base primitives
- CQRS: Command/Query/Event buses and handlers
- Middleware: Transaction, validation, resilience, observability
- Batch: Batch processing utilities
- Export: Data export/import services

**Architecture: Vertical Slices - Shared Infrastructure**
"""

# Base classes (directly from specialized subpackages)
# CQRS
from application.common.cqrs import (
    # Exceptions
    ApplicationError,
    # Types
    Command,
    # Buses
    CommandBus,
    # Handlers
    CommandHandler,
    ConflictError,
    EventHandler,
    EventHandlerError,
    ForbiddenError,
    HandlerNotFoundError,
    MiddlewareFunc,
    NotFoundError,
    Query,
    QueryBus,
    QueryHandler,
    TypedEventBus,
    UnauthorizedError,
    ValidationError,
)
from application.common.dto import ApiResponse, PaginatedResponse, ProblemDetail
from application.common.errors import (
    ApplicationError as BaseApplicationError,
    ConflictError as BaseConflictError,
    ForbiddenError as BaseForbiddenError,
    NotFoundError as BaseNotFoundError,
    UnauthorizedError as BaseUnauthorizedError,
    ValidationError as BaseValidationError,
)
from application.common.mappers import IMapper, Mapper

# Middleware
from application.common.middleware import (
    # Cache
    CacheInvalidationMiddleware,
    # Resilience
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CircuitBreakerOpenError,
    # Validation
    CompositeValidator,
    # Operations
    IdempotencyCache,
    IdempotencyMiddleware,
    # Observability
    LoggingMiddleware,
    MetricsMiddleware,
    QueryCacheMiddleware,
    ResilienceMiddleware,
    RetryConfig,
    RetryExhaustedError,
    RetryMiddleware,
    TransactionMiddleware,
    ValidationMiddleware,
    Validator,
)
from application.common.use_cases import BaseUseCase

__all__ = [
    # DTOs
    "ApiResponse",
    # CQRS - Errors
    "ApplicationError",
    # Base Exceptions (re-exports with Base prefix)
    "BaseApplicationError",
    "BaseConflictError",
    "BaseForbiddenError",
    "BaseNotFoundError",
    "BaseUnauthorizedError",
    # UseCase
    "BaseUseCase",
    "BaseValidationError",
    # Middleware - Cache
    "CacheInvalidationMiddleware",
    # Middleware - Resilience
    "CircuitBreakerConfig",
    "CircuitBreakerMiddleware",
    "CircuitBreakerOpenError",
    # CQRS - Types
    "Command",
    # CQRS - Buses
    "CommandBus",
    # CQRS - Handlers
    "CommandHandler",
    # Middleware - Validation
    "CompositeValidator",
    "ConflictError",
    "EventHandler",
    "EventHandlerError",
    "ForbiddenError",
    "HandlerNotFoundError",
    # Mapper
    "IMapper",
    # Middleware - Operations
    "IdempotencyCache",
    "IdempotencyMiddleware",
    # Middleware - Observability
    "LoggingMiddleware",
    "Mapper",
    "MetricsMiddleware",
    "MiddlewareFunc",
    "NotFoundError",
    "PaginatedResponse",
    "ProblemDetail",
    "Query",
    "QueryBus",
    "QueryCacheMiddleware",
    "QueryHandler",
    "ResilienceMiddleware",
    "RetryConfig",
    "RetryExhaustedError",
    "RetryMiddleware",
    "TransactionMiddleware",
    "TypedEventBus",
    "UnauthorizedError",
    "ValidationError",
    "ValidationMiddleware",
    "Validator",
]
