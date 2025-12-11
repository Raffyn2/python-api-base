"""Common domain components.

**Feature: domain-consolidation-2025**
"""

from domain.common.specification import (
    AndSpecification,
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
from domain.common.value_objects import (
    CurrencyCode,
    Money,
    Percentage,
    Slug,
)

__all__ = [
    # Specification (core)
    "AndSpecification",
    # Specification (domain extensions)
    "AttributeSpecification",
    "ComparisonOperator",
    "CompositeSpecification",
    # Value Objects
    "CurrencyCode",
    "Money",
    "NotSpecification",
    "OrSpecification",
    "Percentage",
    "PredicateSpecification",
    "Slug",
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
