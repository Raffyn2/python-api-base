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
    AppException,
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
    "AppException",
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
    "QueryHandlerError",
    "RateLimitExceededError",
    "TaskStatus",
    "TransactionError",
    "UseCaseError",
    "UserStatus",
    "ValidationError",
    "ValidationStatus",
    # RFC 7807
    "ProblemDetail",
    "ValidationErrorDetail",
    "PROBLEM_JSON_MEDIA_TYPE",
    "setup_exception_handlers",
    "http_exception_handler",
    "validation_exception_handler",
    "generic_exception_handler",
]
