"""Shared application infrastructure.

Provides common components for all bounded contexts:
- Base: DTOs, Mappers, UseCases, Exceptions
- CQRS: Command/Query/Event buses and handlers
- Middleware: Transaction, validation, resilience, observability
- Batch: Batch processing utilities
- Export: Data export/import services

**Architecture: Vertical Slices - Shared Infrastructure**
"""

# Base classes
from application.common.base import (
    # DTOs
    ApiResponse,
    # Exceptions (from base)
    ApplicationError as BaseApplicationError,
    # UseCase
    BaseUseCase,
    ConflictError as BaseConflictError,
    ForbiddenError as BaseForbiddenError,
    # Mapper
    IMapper,
    Mapper,
    NotFoundError as BaseNotFoundError,
    PaginatedResponse,
    ProblemDetail,
    UnauthorizedError as BaseUnauthorizedError,
    ValidationError as BaseValidationError,
)

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

# Middleware
from application.common.middleware import (
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CompositeValidator,
    IdempotencyConfig,
    IdempotencyMiddleware,
    LoggingConfig,
    # Observability
    LoggingMiddleware,
    # Transaction
    Middleware,
    ResilienceMiddleware,
    RetryConfig,
    # Resilience
    RetryMiddleware,
    TransactionMiddleware,
    # Validation
    ValidationMiddleware,
    Validator,
)

__all__ = [
    # DTOs
    "ApiResponse",
    # Exceptions
    "ApplicationError",
    # Base Exceptions (re-exports)
    "BaseApplicationError",
    "BaseConflictError",
    "BaseForbiddenError",
    "BaseNotFoundError",
    "BaseUnauthorizedError",
    # UseCase
    "BaseUseCase",
    "BaseValidationError",
    "CircuitBreakerConfig",
    "CircuitBreakerMiddleware",
    "Command",
    # CQRS
    "CommandBus",
    "CommandHandler",
    "CompositeValidator",
    "ConflictError",
    "EventHandler",
    "EventHandlerError",
    "ForbiddenError",
    "HandlerNotFoundError",
    # Mapper
    "IMapper",
    "IdempotencyConfig",
    "IdempotencyMiddleware",
    "LoggingConfig",
    "LoggingMiddleware",
    "Mapper",
    # Middleware
    "Middleware",
    "MiddlewareFunc",
    "NotFoundError",
    "PaginatedResponse",
    "ProblemDetail",
    "Query",
    "QueryBus",
    "QueryHandler",
    "ResilienceMiddleware",
    "RetryConfig",
    "RetryMiddleware",
    "TransactionMiddleware",
    "TypedEventBus",
    "UnauthorizedError",
    "ValidationError",
    "ValidationMiddleware",
    "Validator",
]
