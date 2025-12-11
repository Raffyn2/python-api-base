"""Error handling module for interface layer.

**Feature: interface-layer-generics-review**
"""

from interface.errors.exceptions import (
    BuilderValidationError,
    CompositionError,
    ConfigurationError,
    FieldError,
    InterfaceError,
    InvalidStatusTransitionError,
    NotFoundError,
    RepositoryError,
    ServiceError,
    TransformationError,
    UnwrapError,
    ValidationError,
)
from interface.errors.messages import (
    ErrorCode,
    ErrorMessage,
)

__all__ = [
    "BuilderValidationError",
    "CompositionError",
    # Configuration
    "ConfigurationError",
    # Messages
    "ErrorCode",
    "ErrorMessage",
    # Validation
    "FieldError",
    # Base
    "InterfaceError",
    "InvalidStatusTransitionError",
    # Resource
    "NotFoundError",
    "RepositoryError",
    "ServiceError",
    # Operations
    "TransformationError",
    "UnwrapError",
    "ValidationError",
]
