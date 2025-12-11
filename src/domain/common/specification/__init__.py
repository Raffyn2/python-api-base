"""Specification pattern for composable business rules.

Re-exports core specification classes and domain-specific extensions.

**Feature: domain-consolidation-2025**
"""

from domain.common.specification.specification import (
    # Core re-exports
    AndSpecification,
    # Domain extensions
    AttributeSpecification,
    ComparisonOperator,
    CompositeSpecification,
    NotSpecification,
    OrSpecification,
    PredicateSpecification,
    Specification,
    contains,
    equals,
    greater_than,
    is_not_null,
    is_null,
    less_than,
    not_equals,
    spec,
)

__all__ = [
    # Core
    "AndSpecification",
    # Domain extensions
    "AttributeSpecification",
    "ComparisonOperator",
    "CompositeSpecification",
    "NotSpecification",
    "OrSpecification",
    "PredicateSpecification",
    "Specification",
    "contains",
    "equals",
    "greater_than",
    "is_not_null",
    "is_null",
    "less_than",
    "not_equals",
    "spec",
]
