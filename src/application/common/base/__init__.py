"""Base classes for application layer.

Provides foundational abstractions:
- DTOs: Generic API response types
- Mapper: Entity-DTO conversion
- UseCase: Base use case pattern
- Exceptions: Application-level errors
"""

from application.common.base.dto import ApiResponse, PaginatedResponse, ProblemDetail
from application.common.base.exceptions import (
    ApplicationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from application.common.base.mapper import IMapper, Mapper
from application.common.base.use_case import BaseUseCase

__all__ = [
    # DTOs
    "ApiResponse",
    # Exceptions
    "ApplicationError",
    # UseCase
    "BaseUseCase",
    "ConflictError",
    "ForbiddenError",
    # Mapper
    "IMapper",
    "Mapper",
    "NotFoundError",
    "PaginatedResponse",
    "ProblemDetail",
    "UnauthorizedError",
    "ValidationError",
]
