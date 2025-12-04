"""Core error hierarchy.

Provides structured error handling:
- base/: Error hierarchy by layer (domain, application, infrastructure)
- http/: HTTP/API error handling (RFC 7807, handlers, constants)
- status: Operation status enums

**Feature: architecture-restructuring-2025**
"""

# Base error hierarchy
from core.errors.base import (
    # Domain
    AppError,
    AppException,  # Backwards compatibility alias
    # Application
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    CommandHandlerError,
    ConcurrencyError,
    ConflictError,
    DatabaseError,
    EntityNotFoundError,
    ErrorContext,
    ExternalServiceError,
    HandlerNotFoundError,
    # Infrastructure
    InfrastructureError,
    InvalidCommandError,
    InvalidQueryError,
    QueryHandlerError,
    RateLimitExceededError,
    TransactionError,
    UseCaseError,
    ValidationError,
)

# HTTP/API
from core.errors.http import (
    PROBLEM_JSON_MEDIA_TYPE,
    ErrorCode,
    ErrorCodes,
    ErrorMessages,
    # Constants
    HttpStatus,
    # Problem Details
    ProblemDetail,
    ValidationErrorDetail,
    generic_exception_handler,
    http_exception_handler,
    # Exception Handlers
    setup_exception_handlers,
    validation_exception_handler,
)

# Status enums
from core.errors.status import (
    EntityStatus,
    OperationStatus,
    TaskStatus,
    UserStatus,
    ValidationStatus,
)

__all__ = [
    "PROBLEM_JSON_MEDIA_TYPE",
    "AppError",
    "AppException",  # Backwards compatibility alias
    "ApplicationError",
    "AuthenticationError",
    "AuthorizationError",
    "BusinessRuleViolationError",
    "CommandHandlerError",
    "ConcurrencyError",
    "ConflictError",
    "DatabaseError",
    "EntityNotFoundError",
    "EntityStatus",
    "ErrorCode",
    "ErrorCodes",
    "ErrorContext",
    "ErrorMessages",
    "ExternalServiceError",
    "HandlerNotFoundError",
    "HttpStatus",
    "InfrastructureError",
    "InvalidCommandError",
    "InvalidQueryError",
    "OperationStatus",
    # RFC 7807
    "ProblemDetail",
    "QueryHandlerError",
    "RateLimitExceededError",
    "TaskStatus",
    "TransactionError",
    "UseCaseError",
    "UserStatus",
    "ValidationError",
    "ValidationErrorDetail",
    "ValidationStatus",
    "generic_exception_handler",
    "http_exception_handler",
    "setup_exception_handlers",
    "validation_exception_handler",
]
