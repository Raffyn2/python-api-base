"""Validation-related exceptions.

**Feature: shared-modules-refactoring**
**Refactored: Split from exceptions.py for one-class-per-file compliance**

Note:
    This ValidationError is for shared module input validation (field/value/constraint).
    For HTTP API validation errors, use core.errors.base.domain_errors.ValidationError.
"""

from __future__ import annotations

from core.errors.shared.base import SharedModuleError


class ValidationError(SharedModuleError):
    """Validation error for input parameters.

    Raised when input validation fails with details about the invalid value.

    Note:
        The value is stored but NOT included in the error message to prevent
        information leakage of sensitive data (passwords, tokens, etc.).

    Attributes:
        field: Name of the field that failed validation.
        value: The invalid value (stored for debugging, not exposed in message).
        constraint: Description of the validation constraint.
    """

    def __init__(
        self,
        field: str,
        value: object,
        constraint: str,
    ) -> None:
        """Initialize validation error.

        Args:
            field: Name of the field that failed validation.
            value: The invalid value (stored but not exposed in message).
            constraint: Description of the validation constraint.
        """
        self.field = field
        self.value = value
        self.constraint = constraint
        # Security: Do not expose value in message to prevent info leak
        super().__init__(f"Validation failed for '{field}': {constraint}")
