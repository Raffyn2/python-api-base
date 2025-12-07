"""Tests for in-memory query builder module."""

import pytest
from pydantic import BaseModel

from infrastructure.db.query_builder.conditions import (
    ComparisonOperator,
    ConditionGroup,
    LogicalOperator,
    QueryCondition,
    SortClause,
    SortDirection,
)
from infrastructure.db.query_builder.in_memory import (
    InMemoryQueryBuilder,
    _compare_between,
)


class SampleModel(BaseModel):
    """Sample model for testing."""

    id: int
    name: str
    age: int
    status: str
    score: float | None = None
    is_deleted: bool = False


@pytest.fixture
def sample_data() -> list[SampleModel]:
    """Create sample data for testing."""
    return [
        SampleModel(id=1, name="Alice", age=30, status="active", score=85.5),
        SampleModel(id=2, name="Bob", age=25, status="inactive", score=72.0),
        SampleModel(id=3, name="Charlie", age=35, status="active", score=90.0),
        SampleModel(id=4, name="Diana", age=28, status="pending", score=None),
        SampleModel(id=5, name="Eve", age=30, status="active", score=88.0, is_deleted=True),
    ]


class TestCompareBetween:
    """Tests for _compare_between helper function."""

    def test_value_in_range(self) -> None:
        assert _compare_between(50, (10, 100)) is True

    def test_value_at_lower_bound(self) -> None:
        assert _compare_between(10, (10, 100)) is True

    def test_value_at_upper_bound(self) -> None:
        assert _compare_between(100, (10, 100)) is True

    def test_value_below_range(self) -> None:
        assert _compare_between(5, (10, 100)) is False

    def test_value_above_range(self) -> None:
        assert _compare_between(150, (10, 100)) is False

    def test_none_value(self) -> None:
        assert _compare_between(None, (10, 100)) is False


class TestInMemoryQueryBuilder:
    """Tests for InMemoryQueryBuilder class."""

    def test_init_empty(self) -> None:
        builder = InMemoryQueryBuilder[SampleModel]()
        assert builder._data == []

    def test_init_with_data(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        assert len(builder._data) == 5

    def test_set_data(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder[SampleModel]()
        result = builder.set_data(sample_data)
        assert len(builder._data) == 5
        assert result is builder  # Returns self for chaining

    @pytest.mark.asyncio
    async def test_execute_returns_all(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._options.include_deleted = True
        result = await builder.execute()
        assert result.total == 5
        assert len(result.items) == 5

    @pytest.mark.asyncio
    async def test_execute_excludes_deleted_by_default(
        self, sample_data: list[SampleModel]
    ) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        result = await builder.execute()
        assert result.total == 4
        assert all(not item.is_deleted for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_eq(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("status", ComparisonOperator.EQ, "active")
        )
        result = await builder.execute()
        assert result.total == 2
        assert all(item.status == "active" for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_ne(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("status", ComparisonOperator.NE, "active")
        )
        result = await builder.execute()
        assert all(item.status != "active" for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_gt(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(QueryCondition("age", ComparisonOperator.GT, 28))
        result = await builder.execute()
        assert all(item.age > 28 for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_ge(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(QueryCondition("age", ComparisonOperator.GE, 30))
        result = await builder.execute()
        assert all(item.age >= 30 for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_lt(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(QueryCondition("age", ComparisonOperator.LT, 30))
        result = await builder.execute()
        assert all(item.age < 30 for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_le(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(QueryCondition("age", ComparisonOperator.LE, 28))
        result = await builder.execute()
        assert all(item.age <= 28 for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_in(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("status", ComparisonOperator.IN, ["active", "pending"])
        )
        result = await builder.execute()
        assert all(item.status in ["active", "pending"] for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_not_in(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("status", ComparisonOperator.NOT_IN, ["inactive"])
        )
        result = await builder.execute()
        assert all(item.status != "inactive" for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_is_null(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("score", ComparisonOperator.IS_NULL, None)
        )
        result = await builder.execute()
        assert result.total == 1
        assert result.items[0].name == "Diana"

    @pytest.mark.asyncio
    async def test_filter_is_not_null(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("score", ComparisonOperator.IS_NOT_NULL, None)
        )
        result = await builder.execute()
        assert all(item.score is not None for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_between(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("age", ComparisonOperator.BETWEEN, (26, 32))
        )
        result = await builder.execute()
        assert all(26 <= item.age <= 32 for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_contains(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("name", ComparisonOperator.CONTAINS, "li")
        )
        result = await builder.execute()
        assert all("li" in item.name for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_starts_with(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("name", ComparisonOperator.STARTS_WITH, "A")
        )
        result = await builder.execute()
        assert result.total == 1
        assert result.items[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_filter_ends_with(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("name", ComparisonOperator.ENDS_WITH, "e")
        )
        result = await builder.execute()
        assert all(item.name.endswith("e") for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_like(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(QueryCondition("name", ComparisonOperator.LIKE, "A%"))
        result = await builder.execute()
        assert result.total == 1
        assert result.items[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_filter_ilike(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(QueryCondition("name", ComparisonOperator.ILIKE, "a%"))
        result = await builder.execute()
        assert result.total == 1
        assert result.items[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_filter_negated(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("status", ComparisonOperator.EQ, "active", negate=True)
        )
        result = await builder.execute()
        assert all(item.status != "active" for item in result.items)

    @pytest.mark.asyncio
    async def test_sort_asc(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._sort_clauses.append(SortClause("age", SortDirection.ASC))
        result = await builder.execute()
        ages = [item.age for item in result.items]
        assert ages == sorted(ages)

    @pytest.mark.asyncio
    async def test_sort_desc(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._sort_clauses.append(SortClause("age", SortDirection.DESC))
        result = await builder.execute()
        ages = [item.age for item in result.items]
        assert ages == sorted(ages, reverse=True)

    @pytest.mark.asyncio
    async def test_pagination_skip(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._options.skip = 2
        result = await builder.execute()
        assert len(result.items) == 2
        assert result.skip == 2

    @pytest.mark.asyncio
    async def test_pagination_limit(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._options.limit = 2
        result = await builder.execute()
        assert len(result.items) == 2
        assert result.limit == 2

    @pytest.mark.asyncio
    async def test_has_more(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._options.limit = 2
        result = await builder.execute()
        assert result.has_more is True

    @pytest.mark.asyncio
    async def test_first_returns_item(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._sort_clauses.append(SortClause("id", SortDirection.ASC))
        result = await builder.first()
        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_first_returns_none_when_empty(self) -> None:
        builder = InMemoryQueryBuilder[SampleModel]([])
        result = await builder.first()
        assert result is None

    @pytest.mark.asyncio
    async def test_count(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        count = await builder.count()
        assert count == 4  # Excludes deleted

    @pytest.mark.asyncio
    async def test_condition_group_and(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        builder._conditions.add(
            QueryCondition("status", ComparisonOperator.EQ, "active")
        )
        builder._conditions.add(QueryCondition("age", ComparisonOperator.GE, 30))
        result = await builder.execute()
        assert all(
            item.status == "active" and item.age >= 30 for item in result.items
        )

    @pytest.mark.asyncio
    async def test_condition_group_or(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        group = ConditionGroup(operator=LogicalOperator.OR)
        group.add(QueryCondition("status", ComparisonOperator.EQ, "active"))
        group.add(QueryCondition("status", ComparisonOperator.EQ, "pending"))
        builder._conditions.add(group)
        result = await builder.execute()
        assert all(
            item.status in ["active", "pending"] for item in result.items
        )

    @pytest.mark.asyncio
    async def test_nested_condition_groups(
        self, sample_data: list[SampleModel]
    ) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        inner = ConditionGroup(operator=LogicalOperator.OR)
        inner.add(QueryCondition("age", ComparisonOperator.LT, 26))
        inner.add(QueryCondition("age", ComparisonOperator.GT, 32))
        builder._conditions.add(inner)
        result = await builder.execute()
        assert all(item.age < 26 or item.age > 32 for item in result.items)


class TestMatchPattern:
    """Tests for SQL LIKE pattern matching."""

    def test_percent_wildcard_start(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        assert builder._match_pattern("Alice", "%ice") is True

    def test_percent_wildcard_end(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        assert builder._match_pattern("Alice", "Ali%") is True

    def test_percent_wildcard_both(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        assert builder._match_pattern("Alice", "%lic%") is True

    def test_underscore_single_char(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        assert builder._match_pattern("Bob", "B_b") is True

    def test_no_match(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        assert builder._match_pattern("Alice", "Bob%") is False

    def test_exact_match(self, sample_data: list[SampleModel]) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        assert builder._match_pattern("Alice", "Alice") is True

    def test_special_regex_chars_escaped(
        self, sample_data: list[SampleModel]
    ) -> None:
        builder = InMemoryQueryBuilder(sample_data)
        # Dot should be literal, not regex wildcard
        assert builder._match_pattern("test.txt", "test.txt") is True
        assert builder._match_pattern("testXtxt", "test.txt") is False
