"""Common validators for command validation.

**Feature: application-layer-code-review-2025**
**Refactored: Split from validation.py for one-class-per-file compliance**
"""

from collections.abc import Sequence
from typing import Any

from application.common.middleware.validation.base import Validator


class RequiredFieldValidator[TCommand](Validator[TCommand]):
    """Validates that required fields are present and non-empty.

    Type Parameters:
        TCommand: The command type to validate.
    """

    def __init__(self, fields: Sequence[str]) -> None:
        """Initialize validator.

        Args:
            fields: List of required field names.
        """
        self._fields = fields

    def validate(self, command: TCommand) -> list[dict[str, Any]]:
        """Check required fields are present.

        Args:
            command: Command to validate.

        Returns:
            List of errors for missing fields.
        """
        errors: list[dict[str, Any]] = []
        for field in self._fields:
            value = getattr(command, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append({
                    "field": field,
                    "message": f"{field} is required",
                    "code": "required",
                })
        return errors


class StringLengthValidator[TCommand](Validator[TCommand]):
    """Validates string field lengths.

    Type Parameters:
        TCommand: The command type to validate.
    """

    def __init__(
        self,
        field: str,
        min_length: int = 0,
        max_length: int | None = None,
    ) -> None:
        """Initialize validator.

        Args:
            field: Field name to validate.
            min_length: Minimum string length.
            max_length: Maximum string length.
        """
        self._field = field
        self._min_length = min_length
        self._max_length = max_length

    def validate(self, command: TCommand) -> list[dict[str, Any]]:
        """Check string length constraints.

        Args:
            command: Command to validate.

        Returns:
            List of errors for length violations.
        """
        errors: list[dict[str, Any]] = []
        value = getattr(command, self._field, None)

        if value is None:
            return errors

        if not isinstance(value, str):
            return errors

        if len(value) < self._min_length:
            errors.append({
                "field": self._field,
                "message": f"{self._field} must be at least {self._min_length} characters",
                "code": "min_length",
            })

        if self._max_length is not None and len(value) > self._max_length:
            errors.append({
                "field": self._field,
                "message": f"{self._field} must not exceed {self._max_length} characters",
                "code": "max_length",
            })

        return errors


class RangeValidator[TCommand](Validator[TCommand]):
    """Validates numeric field ranges.

    Type Parameters:
        TCommand: The command type to validate.
    """

    def __init__(
        self,
        field: str,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> None:
        """Initialize validator.

        Args:
            field: Field name to validate.
            min_value: Minimum allowed value.
            max_value: Maximum allowed value.
        """
        self._field = field
        self._min_value = min_value
        self._max_value = max_value

    def validate(self, command: TCommand) -> list[dict[str, Any]]:
        """Check numeric range constraints.

        Args:
            command: Command to validate.

        Returns:
            List of errors for range violations.
        """
        errors: list[dict[str, Any]] = []
        value = getattr(command, self._field, None)

        if value is None:
            return errors

        if not isinstance(value, int | float):
            return errors

        if self._min_value is not None and value < self._min_value:
            errors.append({
                "field": self._field,
                "message": f"{self._field} must be at least {self._min_value}",
                "code": "min_value",
            })

        if self._max_value is not None and value > self._max_value:
            errors.append({
                "field": self._field,
                "message": f"{self._field} must not exceed {self._max_value}",
                "code": "max_value",
            })

        return errors
