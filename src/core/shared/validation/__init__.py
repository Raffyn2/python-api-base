"""Pydantic V2 validation utilities.

**Feature: api-best-practices-review-2025**

Provides high-performance validation using Pydantic V2 features:
- TypeAdapter for cached validation
- model_validate_json for direct JSON parsing
- computed_field for derived properties
"""

from .pydantic_v2 import (
    ComputedFieldExample,
    EmailStr,
    LowercaseStr,
    OptimizedBaseModel,
    StrippedStr,
    TypeAdapterCache,
    UppercaseStr,
    get_type_adapter,
    validate_bulk,
    validate_bulk_json,
    validate_json_fast,
)

__all__ = [
    "ComputedFieldExample",
    "EmailStr",
    "LowercaseStr",
    "OptimizedBaseModel",
    "StrippedStr",
    "TypeAdapterCache",
    "UppercaseStr",
    "get_type_adapter",
    "validate_bulk",
    "validate_bulk_json",
    "validate_json_fast",
]
