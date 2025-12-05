"""Validation-related exceptions.

**Feature: shared-modules-refactoring**
**Refactored: Split from exceptions.py for one-class-per-file compliance**
"""

from __future__ import annotations

from core.errors.shared.base import SharedModuleError


class ValidationError(SharedModuleError):
    """Validation error for input parameters.

    Raised when input validation fails with details about the invalid value.

    Attributes:
        field: Name of the field that failed validation.
        value: The invalid value.
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
            value: The invalid value.
            constraint: Description of the validation constraint.
        """
        self.field = field
        self.value = value
        self.constraint = constraint
        super().__init__(
            f"Validation failed for '{field}': {constraint} (got: {value})"
        )
