"""Error hierarchy by architectural layer.

- Domain: Business rule violations, entity errors
- Application: Use case, command/query handler errors
- Infrastructure: Database, external service errors
"""

from core.errors.base.application_errors import (
    ApplicationError,
    CommandHandlerError,
    ConcurrencyError,
    HandlerNotFoundError,
    InvalidCommandError,
    InvalidQueryError,
    QueryHandlerError,
    TransactionError,
    UseCaseError,
)
from core.errors.base.domain_errors import (
    AppError,
    AppException,  # Backwards compatibility alias
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    EntityNotFoundError,
    ErrorContext,
    RateLimitExceededError,
    ValidationError,
)
from core.errors.base.infrastructure_errors import (
    DatabaseError,
    ExternalServiceError,
    InfrastructureError,
)

__all__ = [
    # Domain
    "AppError",
    "AppException",  # Backwards compatibility alias
    # Application
    "ApplicationError",
    "AuthenticationError",
    "AuthorizationError",
    "BusinessRuleViolationError",
    "CommandHandlerError",
    "ConcurrencyError",
    "ConflictError",
    "DatabaseError",
    "EntityNotFoundError",
    "ErrorContext",
    "ExternalServiceError",
    "HandlerNotFoundError",
    # Infrastructure
    "InfrastructureError",
    "InvalidCommandError",
    "InvalidQueryError",
    "QueryHandlerError",
    "RateLimitExceededError",
    "TransactionError",
    "UseCaseError",
    "ValidationError",
]
