"""Specification pattern extensions for domain layer.

Re-exports core specification classes and adds domain-specific extensions
like ComparisonOperator and factory functions.

**Feature: domain-consolidation-2025**
"""

from collections.abc import Callable
from enum import Enum
from typing import Any

# Re-export core specification classes
from core.base.patterns.specification import (
    AndSpecification,
    CompositeSpecification,
    NotSpecification,
    OrSpecification,
    PredicateSpecification,
    Specification,
    spec,
)

__all__ = [
    # Core re-exports
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


class ComparisonOperator(Enum):
    """Comparison operators for AttributeSpecification."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GE = "ge"
    LT = "lt"
    LE = "le"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


# Strategy map for comparison operators - reduces cyclomatic complexity
_COMPARISON_STRATEGIES: dict[ComparisonOperator, Callable[[Any, Any], bool]] = {
    ComparisonOperator.EQ: lambda a, v: a == v,
    ComparisonOperator.NE: lambda a, v: a != v,
    ComparisonOperator.GT: lambda a, v: a is not None and a > v,
    ComparisonOperator.GE: lambda a, v: a is not None and a >= v,
    ComparisonOperator.LT: lambda a, v: a is not None and a < v,
    ComparisonOperator.LE: lambda a, v: a is not None and a <= v,
    ComparisonOperator.CONTAINS: lambda a, v: a is not None and v in a,
    ComparisonOperator.STARTS_WITH: lambda a, v: a is not None and str(a).startswith(str(v)),
    ComparisonOperator.ENDS_WITH: lambda a, v: a is not None and str(a).endswith(str(v)),
    ComparisonOperator.IN: lambda a, v: a in (v or []),
    ComparisonOperator.IS_NULL: lambda a, _: a is None,
    ComparisonOperator.IS_NOT_NULL: lambda a, _: a is not None,
}


class AttributeSpecification[T, V](Specification[T]):
    """Specification based on attribute comparison with operators.

    Extended version with multiple comparison operators for domain queries.

    Type Parameters:
        T: The entity type being evaluated.
        V: The value type of the attribute being compared.

    Example:
        >>> age_spec = AttributeSpecification[User, int]("age", ComparisonOperator.GE, 18)
        >>> name_spec = AttributeSpecification[User, str](
        ...     "name", ComparisonOperator.STARTS_WITH, "J"
        ... )
        >>> combined = age_spec & name_spec
    """

    def __init__(
        self,
        attribute: str,
        operator: ComparisonOperator,
        value: V | None = None,
    ) -> None:
        """Initialize attribute specification.

        Args:
            attribute: Name of the attribute to compare.
            operator: Comparison operator to use.
            value: Value to compare against (not needed for IS_NULL/IS_NOT_NULL).
        """
        self._attribute = attribute
        self._operator = operator
        self._value = value

    @property
    def attribute(self) -> str:
        """Get the attribute name."""
        return self._attribute

    @property
    def operator(self) -> ComparisonOperator:
        """Get the comparison operator."""
        return self._operator

    @property
    def value(self) -> V | None:
        """Get the comparison value."""
        return self._value

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies the attribute comparison."""
        attr_value = getattr(candidate, self._attribute, None)
        strategy = _COMPARISON_STRATEGIES.get(self._operator)
        return strategy(attr_value, self._value) if strategy else False

    def to_expression(self) -> tuple[str, str, V | None]:
        """Convert to tuple for SQLAlchemy integration.

        Returns:
            Tuple of (attribute_name, operator, value).
        """
        return (self._attribute, self._operator.value, self._value)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"AttributeSpecification({self._attribute} {self._operator.value} {self._value})"


# Convenience factory functions
def equals[T, V](attribute: str, value: V) -> AttributeSpecification[T, V]:
    """Create an equality specification."""
    return AttributeSpecification(attribute, ComparisonOperator.EQ, value)


def not_equals[T, V](attribute: str, value: V) -> AttributeSpecification[T, V]:
    """Create a not-equal specification."""
    return AttributeSpecification(attribute, ComparisonOperator.NE, value)


def greater_than[T, V](attribute: str, value: V) -> AttributeSpecification[T, V]:
    """Create a greater-than specification."""
    return AttributeSpecification(attribute, ComparisonOperator.GT, value)


def less_than[T, V](attribute: str, value: V) -> AttributeSpecification[T, V]:
    """Create a less-than specification."""
    return AttributeSpecification(attribute, ComparisonOperator.LT, value)


def contains[T](attribute: str, value: str) -> AttributeSpecification[T, str]:
    """Create a contains specification for string attributes."""
    return AttributeSpecification(attribute, ComparisonOperator.CONTAINS, value)


def is_null[T](attribute: str) -> AttributeSpecification[T, None]:
    """Create an is-null specification."""
    return AttributeSpecification(attribute, ComparisonOperator.IS_NULL, None)


def is_not_null[T](attribute: str) -> AttributeSpecification[T, None]:
    """Create an is-not-null specification."""
    return AttributeSpecification(attribute, ComparisonOperator.IS_NOT_NULL, None)
