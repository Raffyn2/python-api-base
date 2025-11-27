"""Advanced Specification pattern with SQL generation.

This module extends the basic Specification pattern with:
- Comparison operators for field-based specifications
- SQL condition generation for SQLAlchemy integration
- Fluent builder API for complex specifications

**Feature: advanced-reusability**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6**
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar

from sqlalchemy import and_ as sql_and
from sqlalchemy import not_ as sql_not
from sqlalchemy import or_ as sql_or

T = TypeVar("T")


class ComparisonOperator(str, Enum):
    """Comparison operators for field specifications.

    Supports standard comparison operations that can be evaluated
    both in-memory and translated to SQL conditions.
    """

    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GE = "ge"  # Greater than or equal
    LT = "lt"  # Less than
    LE = "le"  # Less than or equal
    IN = "in"  # In collection
    LIKE = "like"  # SQL LIKE pattern
    BETWEEN = "between"  # Between two values
    IS_NULL = "is_null"  # Is null check


@dataclass(frozen=True)
class FilterCriteria:
    """Immutable filter criteria for specifications.

    Attributes:
        field: The field name to filter on.
        operator: The comparison operator.
        value: The value(s) to compare against.
    """

    field: str
    operator: ComparisonOperator
    value: Any


class BaseSpecification(ABC, Generic[T]):
    """Abstract base specification with SQL generation support.

    Extends the basic Specification pattern with the ability to
    generate SQLAlchemy filter conditions.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if the candidate satisfies this specification.

        Args:
            candidate: Object to evaluate.

        Returns:
            True if specification is satisfied.
        """
        ...

    @abstractmethod
    def to_sql_condition(self, model_class: type) -> Any:
        """Generate SQLAlchemy filter condition.

        Args:
            model_class: The SQLAlchemy/SQLModel model class.

        Returns:
            SQLAlchemy filter condition.
        """
        ...

    def and_(self, other: "BaseSpecification[T]") -> "CompositeSpecification[T]":
        """Combine with another specification using AND logic.

        Args:
            other: Specification to combine with.

        Returns:
            Combined specification.
        """
        return CompositeSpecification(self, other, "and")

    def or_(self, other: "BaseSpecification[T]") -> "CompositeSpecification[T]":
        """Combine with another specification using OR logic.

        Args:
            other: Specification to combine with.

        Returns:
            Combined specification.
        """
        return CompositeSpecification(self, other, "or")

    def not_(self) -> "NotSpecification[T]":
        """Negate this specification.

        Returns:
            Negated specification.
        """
        return NotSpecification(self)

    def __and__(self, other: "BaseSpecification[T]") -> "CompositeSpecification[T]":
        """Support & operator for AND combination."""
        return self.and_(other)

    def __or__(self, other: "BaseSpecification[T]") -> "CompositeSpecification[T]":
        """Support | operator for OR combination."""
        return self.or_(other)

    def __invert__(self) -> "NotSpecification[T]":
        """Support ~ operator for NOT."""
        return self.not_()


class FieldSpecification(BaseSpecification[T]):
    """Specification based on a field comparison.

    Evaluates a single field against a value using a comparison operator.
    """

    def __init__(
        self,
        field: str,
        operator: ComparisonOperator,
        value: Any,
    ) -> None:
        """Initialize field specification.

        Args:
            field: Field name to compare.
            operator: Comparison operator.
            value: Value to compare against.
        """
        self._field = field
        self._operator = operator
        self._value = value
        self._criteria = FilterCriteria(field, operator, value)

    @property
    def criteria(self) -> FilterCriteria:
        """Get the filter criteria."""
        return self._criteria

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies this field specification.

        Args:
            candidate: Object to evaluate.

        Returns:
            True if field comparison is satisfied.

        Raises:
            ValueError: If field doesn't exist on candidate.
        """
        if not hasattr(candidate, self._field):
            raise ValueError(f"Field '{self._field}' not found on candidate")

        field_value = getattr(candidate, self._field)
        return self._evaluate(field_value)

    def _evaluate(self, field_value: Any) -> bool:
        """Evaluate the comparison.

        Args:
            field_value: The actual field value.

        Returns:
            True if comparison is satisfied.
        """
        op = self._operator
        val = self._value

        if op == ComparisonOperator.EQ:
            return field_value == val
        elif op == ComparisonOperator.NE:
            return field_value != val
        elif op == ComparisonOperator.GT:
            return field_value > val
        elif op == ComparisonOperator.GE:
            return field_value >= val
        elif op == ComparisonOperator.LT:
            return field_value < val
        elif op == ComparisonOperator.LE:
            return field_value <= val
        elif op == ComparisonOperator.IN:
            return field_value in val
        elif op == ComparisonOperator.LIKE:
            # Simple LIKE implementation for in-memory
            pattern = val.replace("%", ".*").replace("_", ".")
            import re
            return bool(re.match(f"^{pattern}$", str(field_value), re.IGNORECASE))
        elif op == ComparisonOperator.BETWEEN:
            low, high = val
            return low <= field_value <= high
        elif op == ComparisonOperator.IS_NULL:
            return (field_value is None) == val

        return False

    def _has_field(self, model_class: type, field: str) -> bool:
        """Check if model has the specified field.

        Handles both SQLModel/SQLAlchemy models and dataclasses.
        """
        # Check for SQLAlchemy column attribute
        if hasattr(model_class, field):
            attr = getattr(model_class, field)
            # SQLAlchemy columns have a 'property' attribute
            if hasattr(attr, "property") or hasattr(attr, "type"):
                return True
        # Check for dataclass fields
        if hasattr(model_class, "__dataclass_fields__"):
            return field in model_class.__dataclass_fields__
        # Check for Pydantic model fields
        if hasattr(model_class, "model_fields"):
            return field in model_class.model_fields
        # Check annotations
        if hasattr(model_class, "__annotations__"):
            return field in model_class.__annotations__
        return hasattr(model_class, field)

    def to_sql_condition(self, model_class: type) -> Any:
        """Generate SQLAlchemy filter condition.

        Args:
            model_class: The SQLAlchemy/SQLModel model class.

        Returns:
            SQLAlchemy filter condition.

        Raises:
            ValueError: If field doesn't exist on model.
        """
        if not self._has_field(model_class, self._field):
            raise ValueError(f"Field '{self._field}' not found on model")

        column = getattr(model_class, self._field, None)
        
        # For dataclasses/Pydantic models without SQLAlchemy columns,
        # create a mock column-like object for testing
        if column is None or not hasattr(column, "property"):
            # Return a simple comparison expression for non-SQLAlchemy models
            from sqlalchemy import literal_column
            column = literal_column(self._field)
        op = self._operator
        val = self._value

        if op == ComparisonOperator.EQ:
            return column == val
        elif op == ComparisonOperator.NE:
            return column != val
        elif op == ComparisonOperator.GT:
            return column > val
        elif op == ComparisonOperator.GE:
            return column >= val
        elif op == ComparisonOperator.LT:
            return column < val
        elif op == ComparisonOperator.LE:
            return column <= val
        elif op == ComparisonOperator.IN:
            return column.in_(val)
        elif op == ComparisonOperator.LIKE:
            return column.like(val)
        elif op == ComparisonOperator.BETWEEN:
            low, high = val
            return column.between(low, high)
        elif op == ComparisonOperator.IS_NULL:
            return column.is_(None) if val else column.isnot(None)

        raise ValueError(f"Unknown operator: {op}")


class CompositeSpecification(BaseSpecification[T]):
    """Specification combining two specifications with AND/OR logic."""

    def __init__(
        self,
        left: BaseSpecification[T],
        right: BaseSpecification[T],
        operator: str,
    ) -> None:
        """Initialize composite specification.

        Args:
            left: Left specification.
            right: Right specification.
            operator: "and" or "or".
        """
        self._left = left
        self._right = right
        self._operator = operator

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies the composite specification.

        Args:
            candidate: Object to evaluate.

        Returns:
            True if composite condition is satisfied.
        """
        left_result = self._left.is_satisfied_by(candidate)
        right_result = self._right.is_satisfied_by(candidate)

        if self._operator == "and":
            return left_result and right_result
        else:  # or
            return left_result or right_result

    def to_sql_condition(self, model_class: type) -> Any:
        """Generate SQLAlchemy filter condition.

        Args:
            model_class: The SQLAlchemy/SQLModel model class.

        Returns:
            SQLAlchemy filter condition.
        """
        left_cond = self._left.to_sql_condition(model_class)
        right_cond = self._right.to_sql_condition(model_class)

        if self._operator == "and":
            return sql_and(left_cond, right_cond)
        else:  # or
            return sql_or(left_cond, right_cond)


class NotSpecification(BaseSpecification[T]):
    """Specification that negates another specification."""

    def __init__(self, spec: BaseSpecification[T]) -> None:
        """Initialize NOT specification.

        Args:
            spec: Specification to negate.
        """
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate does NOT satisfy the specification.

        Args:
            candidate: Object to evaluate.

        Returns:
            True if specification is NOT satisfied.
        """
        return not self._spec.is_satisfied_by(candidate)

    def to_sql_condition(self, model_class: type) -> Any:
        """Generate SQLAlchemy filter condition.

        Args:
            model_class: The SQLAlchemy/SQLModel model class.

        Returns:
            SQLAlchemy NOT filter condition.
        """
        return sql_not(self._spec.to_sql_condition(model_class))


class TrueSpecification(BaseSpecification[T]):
    """Specification that always returns True."""

    def is_satisfied_by(self, candidate: T) -> bool:
        """Always returns True."""
        return True

    def to_sql_condition(self, model_class: type) -> Any:
        """Returns SQL true condition."""
        from sqlalchemy import true
        return true()


class FalseSpecification(BaseSpecification[T]):
    """Specification that always returns False."""

    def is_satisfied_by(self, candidate: T) -> bool:
        """Always returns False."""
        return False

    def to_sql_condition(self, model_class: type) -> Any:
        """Returns SQL false condition."""
        from sqlalchemy import false
        return false()


class SpecificationBuilder(Generic[T]):
    """Fluent builder for creating complex specifications.

    Provides a chainable API for building specifications with
    multiple conditions.

    Example:
        >>> spec = (
        ...     SpecificationBuilder[User]()
        ...     .where("status", ComparisonOperator.EQ, "active")
        ...     .and_where("age", ComparisonOperator.GE, 18)
        ...     .or_where("role", ComparisonOperator.EQ, "admin")
        ...     .build()
        ... )
    """

    def __init__(self) -> None:
        """Initialize the builder with no specification."""
        self._spec: BaseSpecification[T] | None = None

    def where(
        self,
        field: str,
        operator: ComparisonOperator,
        value: Any,
    ) -> "SpecificationBuilder[T]":
        """Set the initial condition.

        Args:
            field: Field name to compare.
            operator: Comparison operator.
            value: Value to compare against.

        Returns:
            Self for chaining.
        """
        self._spec = FieldSpecification(field, operator, value)
        return self

    def and_where(
        self,
        field: str,
        operator: ComparisonOperator,
        value: Any,
    ) -> "SpecificationBuilder[T]":
        """Add an AND condition.

        Args:
            field: Field name to compare.
            operator: Comparison operator.
            value: Value to compare against.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If no initial condition was set.
        """
        if self._spec is None:
            raise ValueError("Must call where() before and_where()")

        new_spec = FieldSpecification[T](field, operator, value)
        self._spec = self._spec.and_(new_spec)
        return self

    def or_where(
        self,
        field: str,
        operator: ComparisonOperator,
        value: Any,
    ) -> "SpecificationBuilder[T]":
        """Add an OR condition.

        Args:
            field: Field name to compare.
            operator: Comparison operator.
            value: Value to compare against.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If no initial condition was set.
        """
        if self._spec is None:
            raise ValueError("Must call where() before or_where()")

        new_spec = FieldSpecification[T](field, operator, value)
        self._spec = self._spec.or_(new_spec)
        return self

    def and_spec(
        self, spec: BaseSpecification[T]
    ) -> "SpecificationBuilder[T]":
        """Add an AND with an existing specification.

        Args:
            spec: Specification to AND with.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If no initial condition was set.
        """
        if self._spec is None:
            raise ValueError("Must call where() before and_spec()")

        self._spec = self._spec.and_(spec)
        return self

    def or_spec(
        self, spec: BaseSpecification[T]
    ) -> "SpecificationBuilder[T]":
        """Add an OR with an existing specification.

        Args:
            spec: Specification to OR with.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If no initial condition was set.
        """
        if self._spec is None:
            raise ValueError("Must call where() before or_spec()")

        self._spec = self._spec.or_(spec)
        return self

    def not_(self) -> "SpecificationBuilder[T]":
        """Negate the current specification.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If no specification was built.
        """
        if self._spec is None:
            raise ValueError("Must call where() before not_()")

        self._spec = self._spec.not_()
        return self

    def build(self) -> BaseSpecification[T]:
        """Build and return the final specification.

        Returns:
            The built specification.

        Raises:
            ValueError: If no specification was built.
        """
        if self._spec is None:
            raise ValueError("No specification built. Call where() first.")

        return self._spec


# Convenience factory functions
def field_eq(field: str, value: Any) -> FieldSpecification:
    """Create an equality specification."""
    return FieldSpecification(field, ComparisonOperator.EQ, value)


def field_ne(field: str, value: Any) -> FieldSpecification:
    """Create a not-equal specification."""
    return FieldSpecification(field, ComparisonOperator.NE, value)


def field_gt(field: str, value: Any) -> FieldSpecification:
    """Create a greater-than specification."""
    return FieldSpecification(field, ComparisonOperator.GT, value)


def field_ge(field: str, value: Any) -> FieldSpecification:
    """Create a greater-than-or-equal specification."""
    return FieldSpecification(field, ComparisonOperator.GE, value)


def field_lt(field: str, value: Any) -> FieldSpecification:
    """Create a less-than specification."""
    return FieldSpecification(field, ComparisonOperator.LT, value)


def field_le(field: str, value: Any) -> FieldSpecification:
    """Create a less-than-or-equal specification."""
    return FieldSpecification(field, ComparisonOperator.LE, value)


def field_in(field: str, values: list[Any]) -> FieldSpecification:
    """Create an IN specification."""
    return FieldSpecification(field, ComparisonOperator.IN, values)


def field_like(field: str, pattern: str) -> FieldSpecification:
    """Create a LIKE specification."""
    return FieldSpecification(field, ComparisonOperator.LIKE, pattern)


def field_between(field: str, low: Any, high: Any) -> FieldSpecification:
    """Create a BETWEEN specification."""
    return FieldSpecification(field, ComparisonOperator.BETWEEN, (low, high))


def field_is_null(field: str, is_null: bool = True) -> FieldSpecification:
    """Create an IS NULL specification."""
    return FieldSpecification(field, ComparisonOperator.IS_NULL, is_null)
