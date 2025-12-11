"""Base validator classes for CQRS middleware.

**Feature: application-layer-code-review-2025**
**Refactored: Split from validation.py for one-class-per-file compliance**

Note: This Validator is for CQRS CommandBus middleware integration.
It uses a simple list[dict] return type for easy error aggregation.

For Result-pattern validators, see: core.base.patterns.validation.Validator
Architecture decision: Two validator APIs serve different purposes:
- This one: Simple API for middleware, returns list of error dicts
- Core one: Result pattern API, returns Result[T, ValidationError[T]]
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


class Validator[TCommand](ABC):
    """Abstract base class for command validators.

    This validator is designed for CQRS middleware integration where
    multiple validators run and errors are aggregated.

    For Result-pattern validators, use core.base.patterns.validation.Validator.

    Type Parameters:
        TCommand: The command type to validate.
    """

    @abstractmethod
    def validate(self, command: TCommand) -> list[dict[str, Any]]:
        """Validate a command.

        Args:
            command: Command to validate.

        Returns:
            List of validation errors as dicts. Empty list if valid.
            Each dict should have 'field', 'message', and optionally 'code'.
        """
        ...


class CompositeValidator[TCommand](Validator[TCommand]):
    """Combines multiple validators into one.

    Type Parameters:
        TCommand: The command type to validate.
    """

    def __init__(self, validators: Sequence[Validator[TCommand]]) -> None:
        """Initialize composite validator.

        Args:
            validators: List of validators to combine.
        """
        self._validators = validators

    def validate(self, command: TCommand) -> list[dict[str, Any]]:
        """Run all validators and collect errors.

        Args:
            command: Command to validate.

        Returns:
            Combined list of validation errors from all validators.
        """
        errors: list[dict[str, Any]] = []
        for validator in self._validators:
            errors.extend(validator.validate(command))
        return errors
