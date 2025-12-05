"""Base validator classes.

**Feature: application-layer-code-review-2025**
**Refactored: Split from validation.py for one-class-per-file compliance**
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any


class Validator[TCommand](ABC):
    """Abstract base class for command validators.

    Type Parameters:
        TCommand: The command type to validate.
    """

    @abstractmethod
    def validate(self, command: TCommand) -> list[dict[str, Any]]:
        """Validate a command.

        Args:
            command: Command to validate.

        Returns:
            List of validation errors. Empty list if valid.
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
