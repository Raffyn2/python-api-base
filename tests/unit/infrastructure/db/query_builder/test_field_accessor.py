"""Tests for query builder field accessor module."""

import pytest

from infrastructure.db.query_builder.conditions import (
    ComparisonOperator,
    SortDirection,
)
from infrastructure.db.query_builder.field_accessor import FieldAccessor, field_


class TestFieldAccessor:
    """Tests for FieldAccessor class."""

    def test_init_with_name_only(self) -> None:
        accessor = FieldAccessor("name")
        assert accessor.name == "name"

    def test_init_with_type(self) -> None:
        accessor = FieldAccessor("age", int)
        assert accessor.name == "age"
        assert accessor._field_type == int

    def test_name_property(self) -> None:
        accessor = FieldAccessor("email")
        assert accessor.name == "email"

    def test_eq_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("name")
        cond = accessor.eq("test")
        assert cond.field == "name"
        assert cond.operator == ComparisonOperator.EQ
        assert cond.value == "test"

    def test_ne_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("status")
        cond = accessor.ne("deleted")
        assert cond.operator == ComparisonOperator.NE
        assert cond.value == "deleted"

    def test_gt_creates_condition(self) -> None:
        accessor = FieldAccessor[object, int]("age")
        cond = accessor.gt(18)
        assert cond.operator == ComparisonOperator.GT
        assert cond.value == 18

    def test_ge_creates_condition(self) -> None:
        accessor = FieldAccessor[object, int]("score")
        cond = accessor.ge(100)
        assert cond.operator == ComparisonOperator.GE
        assert cond.value == 100

    def test_lt_creates_condition(self) -> None:
        accessor = FieldAccessor[object, float]("price")
        cond = accessor.lt(50.0)
        assert cond.operator == ComparisonOperator.LT
        assert cond.value == 50.0

    def test_le_creates_condition(self) -> None:
        accessor = FieldAccessor[object, int]("quantity")
        cond = accessor.le(10)
        assert cond.operator == ComparisonOperator.LE
        assert cond.value == 10

    def test_in_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("status")
        cond = accessor.in_(["active", "pending"])
        assert cond.operator == ComparisonOperator.IN
        assert cond.value == ["active", "pending"]

    def test_in_converts_sequence_to_list(self) -> None:
        accessor = FieldAccessor[object, int]("id")
        cond = accessor.in_((1, 2, 3))
        assert cond.value == [1, 2, 3]

    def test_not_in_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("role")
        cond = accessor.not_in(["admin", "superuser"])
        assert cond.operator == ComparisonOperator.NOT_IN
        assert cond.value == ["admin", "superuser"]

    def test_like_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("name")
        cond = accessor.like("%test%")
        assert cond.operator == ComparisonOperator.LIKE
        assert cond.value == "%test%"

    def test_ilike_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("email")
        cond = accessor.ilike("%@example.com")
        assert cond.operator == ComparisonOperator.ILIKE
        assert cond.value == "%@example.com"

    def test_is_null_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str | None]("deleted_at")
        cond = accessor.is_null()
        assert cond.operator == ComparisonOperator.IS_NULL
        assert cond.value is None

    def test_is_not_null_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str | None]("verified_at")
        cond = accessor.is_not_null()
        assert cond.operator == ComparisonOperator.IS_NOT_NULL
        assert cond.value is None

    def test_between_creates_condition(self) -> None:
        accessor = FieldAccessor[object, int]("price")
        cond = accessor.between(10, 100)
        assert cond.operator == ComparisonOperator.BETWEEN
        assert cond.value == (10, 100)

    def test_contains_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("description")
        cond = accessor.contains("keyword")
        assert cond.operator == ComparisonOperator.CONTAINS
        assert cond.value == "keyword"

    def test_starts_with_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("code")
        cond = accessor.starts_with("PRD-")
        assert cond.operator == ComparisonOperator.STARTS_WITH
        assert cond.value == "PRD-"

    def test_ends_with_creates_condition(self) -> None:
        accessor = FieldAccessor[object, str]("filename")
        cond = accessor.ends_with(".pdf")
        assert cond.operator == ComparisonOperator.ENDS_WITH
        assert cond.value == ".pdf"

    def test_asc_creates_sort_clause(self) -> None:
        accessor = FieldAccessor[object, str]("name")
        clause = accessor.asc()
        assert clause.field == "name"
        assert clause.direction == SortDirection.ASC

    def test_desc_creates_sort_clause(self) -> None:
        accessor = FieldAccessor[object, str]("created_at")
        clause = accessor.desc()
        assert clause.field == "created_at"
        assert clause.direction == SortDirection.DESC


class TestFieldFunction:
    """Tests for field_ factory function."""

    def test_creates_field_accessor(self) -> None:
        accessor = field_("name")
        assert isinstance(accessor, FieldAccessor)
        assert accessor.name == "name"

    def test_creates_with_type(self) -> None:
        accessor = field_("age", int)
        assert accessor.name == "age"
        assert accessor._field_type == int

    def test_can_chain_operations(self) -> None:
        cond = field_("status").eq("active")
        assert cond.field == "status"
        assert cond.value == "active"

    def test_can_create_sort(self) -> None:
        clause = field_("updated_at").desc()
        assert clause.field == "updated_at"
        assert clause.direction == SortDirection.DESC
