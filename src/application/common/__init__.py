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
    # CQRS
    "CommandBus",
    "QueryBus",
    "TypedEventBus",
    "CommandHandler",
    "QueryHandler",
    "EventHandler",
    "Command",
    "Query",
    "MiddlewareFunc",
    # Middleware
    "Middleware",
    "TransactionMiddleware",
    "ValidationMiddleware",
    "Validator",
    "CompositeValidator",
    "RetryMiddleware",
    "RetryConfig",
    "CircuitBreakerMiddleware",
    "CircuitBreakerConfig",
    "ResilienceMiddleware",
    "LoggingMiddleware",
    "LoggingConfig",
    "IdempotencyMiddleware",
    "IdempotencyConfig",
    # DTOs
    "ApiResponse",
    "PaginatedResponse",
    "ProblemDetail",
    # Exceptions
    "ApplicationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "HandlerNotFoundError",
    "EventHandlerError",
    # Mapper
    "IMapper",
    "Mapper",
    # UseCase
    "BaseUseCase",
]
