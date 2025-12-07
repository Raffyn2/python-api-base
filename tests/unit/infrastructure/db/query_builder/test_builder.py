"""Tests for query builder base module."""

import pytest
from pydantic import BaseModel

from infrastructure.db.query_builder.builder import (
    QueryBuilder,
    QueryOptions,
    QueryResult,
)
from infrastructure.db.query_builder.conditions import (
    ComparisonOperator,
    ConditionGroup,
    LogicalOperator,
    QueryCondition,
    SortClause,
    SortDirection,
)
from infrastructure.db.query_builder.in_memory import InMemoryQueryBuilder


class SampleModel(BaseModel):
    """Sample model for testing."""

    id: int
    name: str
    status: str


class TestQueryOptions:
    """Tests for QueryOptions dataclass."""

    def test_default_values(self) -> None:
        options = QueryOptions()
        assert options.skip == 0
        assert options.limit == 100
        assert options.include_deleted is False
        assert options.distinct is False
        assert options.count_only is False

    def test_custom_skip(self) -> None:
        options = QueryOptions(skip=10)
        assert options.skip == 10

    def test_custom_limit(self) -> None:
        options = QueryOptions(limit=50)
        assert options.limit == 50

    def test_include_deleted(self) -> None:
        options = QueryOptions(include_deleted=True)
        assert options.include_deleted is True

    def test_distinct(self) -> None:
        options = QueryOptions(distinct=True)
        assert options.distinct is True

    def test_count_only(self) -> None:
        options = QueryOptions(count_only=True)
        assert options.count_only is True


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_create_result(self) -> None:
        items = [SampleModel(id=1, name="Test", status="active")]
        result = QueryResult(items=items, total=1, skip=0, limit=10, has_more=False)
        assert len(result.items) == 1
        assert result.total == 1
        assert result.skip == 0
        assert result.limit == 10
        assert result.has_more is False

    def test_page_property_first_page(self) -> None:
        result = QueryResult(items=[], total=100, skip=0, limit=10, has_more=True)
        assert result.page == 1

    def test_page_property_second_page(self) -> None:
        result = QueryResult(items=[], total=100, skip=10, limit=10, has_more=True)
        assert result.page == 2

    def test_page_property_third_page(self) -> None:
        result = QueryResult(items=[], total=100, skip=20, limit=10, has_more=True)
        assert result.page == 3

    def test_page_property_zero_limit(self) -> None:
        result = QueryResult(items=[], total=100, skip=0, limit=0, has_more=False)
        assert result.page == 1

    def test_total_pages_exact_division(self) -> None:
        result = QueryResult(items=[], total=100, skip=0, limit=10, has_more=True)
        assert result.total_pages == 10

    def test_total_pages_with_remainder(self) -> None:
        result = QueryResult(items=[], total=95, skip=0, limit=10, has_more=True)
        assert result.total_pages == 10

    def test_total_pages_single_page(self) -> None:
        result = QueryResult(items=[], total=5, skip=0, limit=10, has_more=False)
        assert result.total_pages == 1

    def test_total_pages_zero_limit(self) -> None:
        result = QueryResult(items=[], total=100, skip=0, limit=0, has_more=False)
        assert result.total_pages == 1


class TestQueryBuilderMethods:
    """Tests for QueryBuilder fluent methods using InMemoryQueryBuilder."""

    @pytest.fixture
    def builder(self) -> InMemoryQueryBuilder[SampleModel]:
        data = [
            SampleModel(id=1, name="Alice", status="active"),
            SampleModel(id=2, name="Bob", status="inactive"),
            SampleModel(id=3, name="Charlie", status="active"),
        ]
        return InMemoryQueryBuilder(data)

    def test_where_adds_condition(self, builder: InMemoryQueryBuilder) -> None:
        cond = QueryCondition("status", ComparisonOperator.EQ, "active")
        result = builder.where(cond)
        assert result is builder  # Returns self
        assert len(builder._conditions.conditions) == 1

    def test_and_where_adds_condition(self, builder: InMemoryQueryBuilder) -> None:
        cond1 = QueryCondition("status", ComparisonOperator.EQ, "active")
        cond2 = QueryCondition("id", ComparisonOperator.GT, 1)
        builder.where(cond1).and_where(cond2)
        assert len(builder._conditions.conditions) == 2

    def test_or_where_on_empty(self, builder: InMemoryQueryBuilder) -> None:
        cond = QueryCondition("status", ComparisonOperator.EQ, "active")
        builder.or_where(cond)
        assert len(builder._conditions.conditions) == 1

    def test_or_where_creates_or_group(self, builder: InMemoryQueryBuilder) -> None:
        cond1 = QueryCondition("status", ComparisonOperator.EQ, "active")
        cond2 = QueryCondition("status", ComparisonOperator.EQ, "pending")
        builder.where(cond1).or_where(cond2)
        assert builder._conditions.operator == LogicalOperator.OR

    def test_order_by_adds_clauses(self, builder: InMemoryQueryBuilder) -> None:
        clause = SortClause("name", SortDirection.ASC)
        result = builder.order_by(clause)
        assert result is builder
        assert len(builder._sort_clauses) == 1

    def test_order_by_field(self, builder: InMemoryQueryBuilder) -> None:
        builder.order_by_field("name", SortDirection.DESC)
        assert len(builder._sort_clauses) == 1
        assert builder._sort_clauses[0].field == "name"
        assert builder._sort_clauses[0].direction == SortDirection.DESC

    def test_skip_sets_value(self, builder: InMemoryQueryBuilder) -> None:
        result = builder.skip(10)
        assert result is builder
        assert builder._options.skip == 10

    def test_skip_negative_becomes_zero(self, builder: InMemoryQueryBuilder) -> None:
        builder.skip(-5)
        assert builder._options.skip == 0

    def test_limit_sets_value(self, builder: InMemoryQueryBuilder) -> None:
        result = builder.limit(50)
        assert result is builder
        assert builder._options.limit == 50

    def test_limit_negative_becomes_zero(self, builder: InMemoryQueryBuilder) -> None:
        builder.limit(-10)
        assert builder._options.limit == 0

    def test_page_sets_skip_and_limit(self, builder: InMemoryQueryBuilder) -> None:
        builder.page(3, 20)
        assert builder._options.skip == 40  # (3-1) * 20
        assert builder._options.limit == 20

    def test_page_minimum_is_one(self, builder: InMemoryQueryBuilder) -> None:
        builder.page(0, 10)
        assert builder._options.skip == 0  # Page 1

    def test_include_deleted(self, builder: InMemoryQueryBuilder) -> None:
        result = builder.include_deleted(True)
        assert result is builder
        assert builder._options.include_deleted is True

    def test_distinct(self, builder: InMemoryQueryBuilder) -> None:
        result = builder.distinct(True)
        assert result is builder
        assert builder._options.distinct is True

    def test_select_fields(self, builder: InMemoryQueryBuilder) -> None:
        result = builder.select("id", "name")
        assert result is builder
        assert builder._select_fields == ["id", "name"]

    def test_count_only(self, builder: InMemoryQueryBuilder) -> None:
        result = builder.count_only(True)
        assert result is builder
        assert builder._options.count_only is True

    def test_reset_clears_all(self, builder: InMemoryQueryBuilder) -> None:
        builder.where(QueryCondition("id", ComparisonOperator.EQ, 1))
        builder.order_by_field("name")
        builder.skip(10).limit(50)
        builder.select("id")
        builder.reset()
        assert builder._conditions.is_empty()
        assert builder._sort_clauses == []
        assert builder._options.skip == 0
        assert builder._options.limit == 100
        assert builder._select_fields is None

    def test_clone_creates_copy(self, builder: InMemoryQueryBuilder) -> None:
        builder.where(QueryCondition("id", ComparisonOperator.EQ, 1))
        builder.skip(10)
        cloned = builder.clone()
        assert cloned is not builder
        assert len(cloned._conditions.conditions) == 1
        assert cloned._options.skip == 10

    def test_to_dict(self, builder: InMemoryQueryBuilder) -> None:
        builder.where(QueryCondition("status", ComparisonOperator.EQ, "active"))
        builder.order_by_field("name")
        builder.skip(10).limit(20)
        result = builder.to_dict()
        assert "conditions" in result
        assert "sort" in result
        assert "options" in result
        assert result["options"]["skip"] == 10
        assert result["options"]["limit"] == 20
