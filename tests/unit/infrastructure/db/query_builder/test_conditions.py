"""Tests for query builder conditions module.

Tests the conditions, operators, and sort clauses used in query building.
Note: Imports directly from conditions module to avoid circular import in __init__.py
"""

import pytest

# Direct import from conditions module (not package __init__)
from infrastructure.db.query_builder.conditions import (
    ComparisonOperator,
    ConditionGroup,
    LogicalOperator,
    QueryCondition,
    SortClause,
    SortDirection,
)


class TestSortDirection:
    """Tests for SortDirection enum."""

    def test_asc_value(self) -> None:
        assert SortDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert SortDirection.DESC.value == "desc"

    def test_all_values_are_strings(self) -> None:
        for direction in SortDirection:
            assert isinstance(direction.value, str)


class TestComparisonOperator:
    """Tests for ComparisonOperator enum."""

    def test_eq_value(self) -> None:
        assert ComparisonOperator.EQ.value == "eq"

    def test_ne_value(self) -> None:
        assert ComparisonOperator.NE.value == "ne"

    def test_gt_value(self) -> None:
        assert ComparisonOperator.GT.value == "gt"

    def test_ge_value(self) -> None:
        assert ComparisonOperator.GE.value == "ge"

    def test_lt_value(self) -> None:
        assert ComparisonOperator.LT.value == "lt"

    def test_le_value(self) -> None:
        assert ComparisonOperator.LE.value == "le"

    def test_in_value(self) -> None:
        assert ComparisonOperator.IN.value == "in"

    def test_not_in_value(self) -> None:
        assert ComparisonOperator.NOT_IN.value == "not_in"

    def test_like_value(self) -> None:
        assert ComparisonOperator.LIKE.value == "like"

    def test_ilike_value(self) -> None:
        assert ComparisonOperator.ILIKE.value == "ilike"

    def test_is_null_value(self) -> None:
        assert ComparisonOperator.IS_NULL.value == "is_null"

    def test_is_not_null_value(self) -> None:
        assert ComparisonOperator.IS_NOT_NULL.value == "is_not_null"

    def test_between_value(self) -> None:
        assert ComparisonOperator.BETWEEN.value == "between"

    def test_contains_value(self) -> None:
        assert ComparisonOperator.CONTAINS.value == "contains"

    def test_starts_with_value(self) -> None:
        assert ComparisonOperator.STARTS_WITH.value == "starts_with"

    def test_ends_with_value(self) -> None:
        assert ComparisonOperator.ENDS_WITH.value == "ends_with"


class TestLogicalOperator:
    """Tests for LogicalOperator enum."""

    def test_and_value(self) -> None:
        assert LogicalOperator.AND.value == "and"

    def test_or_value(self) -> None:
        assert LogicalOperator.OR.value == "or"

    def test_not_value(self) -> None:
        assert LogicalOperator.NOT.value == "not"


class TestQueryCondition:
    """Tests for QueryCondition dataclass."""

    def test_create_simple_condition(self) -> None:
        cond = QueryCondition("name", ComparisonOperator.EQ, "test")
        assert cond.field == "name"
        assert cond.operator == ComparisonOperator.EQ
        assert cond.value == "test"
        assert cond.negate is False

    def test_create_negated_condition(self) -> None:
        cond = QueryCondition("age", ComparisonOperator.GT, 18, negate=True)
        assert cond.negate is True

    def test_condition_is_frozen(self) -> None:
        cond = QueryCondition("name", ComparisonOperator.EQ, "test")
        with pytest.raises(AttributeError):
            cond.field = "other"  # type: ignore

    def test_to_dict(self) -> None:
        cond = QueryCondition("status", ComparisonOperator.IN, ["active", "pending"])
        result = cond.to_dict()
        assert result == {
            "field": "status",
            "operator": "in",
            "value": ["active", "pending"],
            "negate": False,
        }

    def test_to_dict_with_negate(self) -> None:
        cond = QueryCondition("deleted", ComparisonOperator.EQ, True, negate=True)
        result = cond.to_dict()
        assert result["negate"] is True

    def test_condition_with_none_value(self) -> None:
        cond = QueryCondition("field", ComparisonOperator.IS_NULL, None)
        assert cond.value is None

    def test_condition_with_tuple_value(self) -> None:
        cond = QueryCondition("price", ComparisonOperator.BETWEEN, (10, 100))
        assert cond.value == (10, 100)


class TestSortClause:
    """Tests for SortClause dataclass."""

    def test_create_default_asc(self) -> None:
        clause = SortClause("name")
        assert clause.field == "name"
        assert clause.direction == SortDirection.ASC

    def test_create_desc(self) -> None:
        clause = SortClause("created_at", SortDirection.DESC)
        assert clause.direction == SortDirection.DESC

    def test_clause_is_frozen(self) -> None:
        clause = SortClause("name")
        with pytest.raises(AttributeError):
            clause.field = "other"  # type: ignore

    def test_to_dict_asc(self) -> None:
        clause = SortClause("name", SortDirection.ASC)
        result = clause.to_dict()
        assert result == {"field": "name", "direction": "asc"}

    def test_to_dict_desc(self) -> None:
        clause = SortClause("updated_at", SortDirection.DESC)
        result = clause.to_dict()
        assert result == {"field": "updated_at", "direction": "desc"}


class TestConditionGroup:
    """Tests for ConditionGroup dataclass."""

    def test_create_empty_group(self) -> None:
        group = ConditionGroup()
        assert group.conditions == []
        assert group.operator == LogicalOperator.AND
        assert group.is_empty() is True

    def test_create_with_or_operator(self) -> None:
        group = ConditionGroup(operator=LogicalOperator.OR)
        assert group.operator == LogicalOperator.OR

    def test_add_condition(self) -> None:
        group = ConditionGroup()
        cond = QueryCondition("name", ComparisonOperator.EQ, "test")
        group.add(cond)
        assert len(group.conditions) == 1
        assert group.is_empty() is False

    def test_add_multiple_conditions(self) -> None:
        group = ConditionGroup()
        group.add(QueryCondition("name", ComparisonOperator.EQ, "test"))
        group.add(QueryCondition("age", ComparisonOperator.GT, 18))
        assert len(group.conditions) == 2

    def test_add_nested_group(self) -> None:
        outer = ConditionGroup()
        inner = ConditionGroup(operator=LogicalOperator.OR)
        inner.add(QueryCondition("status", ComparisonOperator.EQ, "active"))
        inner.add(QueryCondition("status", ComparisonOperator.EQ, "pending"))
        outer.add(inner)
        assert len(outer.conditions) == 1
        assert isinstance(outer.conditions[0], ConditionGroup)

    def test_is_empty_with_conditions(self) -> None:
        group = ConditionGroup()
        group.add(QueryCondition("x", ComparisonOperator.EQ, 1))
        assert group.is_empty() is False

    def test_group_is_mutable(self) -> None:
        group = ConditionGroup()
        group.operator = LogicalOperator.NOT
        assert group.operator == LogicalOperator.NOT
