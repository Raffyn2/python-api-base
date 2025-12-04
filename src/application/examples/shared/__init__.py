"""Shared components for Example system.

**Feature: example-system-demo**
"""

from application.examples.shared.dtos import MoneyDTO
from application.examples.shared.errors import (
    NotFoundError,
    UseCaseError,
    ValidationError,
)

__all__ = [
    "MoneyDTO",
    "NotFoundError",
    "UseCaseError",
    "ValidationError",
]
