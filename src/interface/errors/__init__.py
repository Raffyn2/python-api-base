"""Error handling module for interface layer.

**Feature: interface-layer-generics-review**
"""

from interface.errors.exceptions import (
    BuilderValidationError,
    ConfigurationError,
    FieldError,
    InterfaceError,
    InvalidStatusTransitionError,
    NotFoundError,
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
    "ConfigurationError",
    "ErrorCode",
    "ErrorMessage",
    "FieldError",
    "InterfaceError",
    "InvalidStatusTransitionError",
    "NotFoundError",
    "TransformationError",
    "UnwrapError",
    "ValidationError",
]
