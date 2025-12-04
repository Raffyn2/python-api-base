from __future__ import annotations

from typing import Any, Self
from collections.abc import Sequence, Callable
import pytest
from pydantic import BaseModel

from infrastructure.db.query_builder.builder import (
    QueryBuilder,
    QueryResult,
    QueryOptions,
)
from infrastructure.db.query_builder.conditions import (
    QueryCondition,
    SortClause,
    SortDirection,
    ConditionGroup,
    LogicalOperator,
    ComparisonOperator,
)
from domain.common.specification.specification import Specification


class MockModel(BaseModel):
    id: int
    name: str
    value: int
    is_deleted: bool = False


class MockQueryBuilder(QueryBuilder[MockModel]):
    def __init__(self, items: Sequence[MockModel] | None = None) -> None:
        super().__init__()
        self._items = items or []

    def _create_sub_builder(self) -> Self:
        return MockQueryBuilder(self._items)

    async def execute(self) -> QueryResult[MockModel]:
        items = list(self._items)
        if self._options.skip > 0:
            items = items[self._options.skip :]
        if self._options.limit > 0:
            items = items[: self._options.limit]

        total = len(self._items)
        return QueryResult(
            items=items,
            total=total,
            skip=self._options.skip,
            limit=self._options.limit,
            has_more=(self._options.skip + len(items)) < total,
        )

    async def first(self) -> MockModel | None:
        if self._items:
            return self._items[0]
        return None

    async def count(self) -> int:
        return len(self._items)


@pytest.fixture
def sample_items() -> list[MockModel]:
    return [
        MockModel(id=1, name="A", value=10),
        MockModel(id=2, name="B", value=20),
        MockModel(id=3, name="C", value=30),
        MockModel(id=4, name="D", value=40),
        MockModel(id=5, name="E", value=50),
    ]


@pytest.fixture
def builder(sample_items: list[MockModel]) -> MockQueryBuilder:
    return MockQueryBuilder(sample_items)


class TestQueryResult:
    def test_page_calculation(self) -> None:
        result = QueryResult(items=[], total=100, skip=20, limit=10, has_more=True)
        assert result.page == 3

    def test_total_pages_calculation(self) -> None:
        result = QueryResult(items=[], total=100, skip=0, limit=10, has_more=True)
        assert result.total_pages == 10

    def test_total_pages_with_uneven_total(self) -> None:
        result = QueryResult(items=[], total=95, skip=0, limit=10, has_more=True)
        assert result.total_pages == 10

    def test_page_with_zero_limit(self) -> None:
        result = QueryResult(items=[], total=100, skip=0, limit=0, has_more=False)
        assert result.page == 1
        assert result.total_pages == 1


class TestQueryBuilder:
    @pytest.mark.asyncio
    async def test_where(self, builder: MockQueryBuilder) -> None:
        condition = QueryCondition(field="id", value=1, operator=ComparisonOperator.EQ)
        builder.where(condition)
        assert builder._conditions.conditions == [condition]

    @pytest.mark.asyncio
    async def test_and_where(self, builder: MockQueryBuilder) -> None:
        condition = QueryCondition(field="id", value=1, operator=ComparisonOperator.EQ)
        builder.and_where(condition)
        assert builder._conditions.conditions == [condition]

    @pytest.mark.asyncio
    async def test_or_where(self, builder: MockQueryBuilder) -> None:
        builder.where(QueryCondition(field="id", value=1, operator=ComparisonOperator.EQ))
        builder.or_where(QueryCondition(field="id", value=2, operator=ComparisonOperator.EQ))
        assert builder._conditions.operator == LogicalOperator.OR
        assert len(builder._conditions.conditions) == 2

    @pytest.mark.asyncio
    async def test_where_group(self, builder: MockQueryBuilder) -> None:
        def group_fn(b: QueryBuilder[MockModel]) -> QueryBuilder[MockModel]:
            return b.where(
                QueryCondition(field="name", value="A", operator=ComparisonOperator.EQ)
            ).or_where(
                QueryCondition(field="value", value=30, operator=ComparisonOperator.EQ)
            )

        builder.where(
            QueryCondition(field="id", value=1, operator=ComparisonOperator.EQ)
        ).where_group(group_fn)

        assert len(builder._conditions.conditions) == 2
        group = builder._conditions.conditions[1]
        assert isinstance(group, ConditionGroup)
        assert group.operator == LogicalOperator.AND
        assert len(group.conditions) == 2
        assert group.conditions[0].field == "name"
        assert group.conditions[1].field == "value"
        
    @pytest.mark.asyncio
    async def test_order_by(self, builder: MockQueryBuilder) -> None:
        clause = SortClause(field="name", direction=SortDirection.DESC)
        builder.order_by(clause)
        assert builder._sort_clauses == [clause]

    @pytest.mark.asyncio
    async def test_order_by_field(self, builder: MockQueryBuilder) -> None:
        builder.order_by_field("name", SortDirection.DESC)
        assert builder._sort_clauses == [
            SortClause(field="name", direction=SortDirection.DESC)
        ]

    @pytest.mark.asyncio
    async def test_skip(self, builder: MockQueryBuilder) -> None:
        builder.skip(10)
        assert builder._options.skip == 10

    @pytest.mark.asyncio
    async def test_limit(self, builder: MockQueryBuilder) -> None:
        builder.limit(50)
        assert builder._options.limit == 50

    @pytest.mark.asyncio
    async def test_page(self, builder: MockQueryBuilder) -> None:
        builder.page(3, 25)
        assert builder._options.skip == 50
        assert builder._options.limit == 25

    @pytest.mark.asyncio
    async def test_include_deleted(self, builder: MockQueryBuilder) -> None:
        builder.include_deleted()
        assert builder._options.include_deleted is True

    @pytest.mark.asyncio
    async def test_distinct(self, builder: MockQueryBuilder) -> None:
        builder.distinct()
        assert builder._options.distinct is True

    @pytest.mark.asyncio
    async def test_select(self, builder: MockQueryBuilder) -> None:
        builder.select("id", "name")
        assert builder._select_fields == ["id", "name"]

    @pytest.mark.asyncio
    async def test_count_only(self, builder: MockQueryBuilder) -> None:
        builder.count_only()
        assert builder._options.count_only is True

    @pytest.mark.asyncio
    async def test_reset(self, builder: MockQueryBuilder) -> None:
        builder.where(
            QueryCondition(field="id", value=1, operator=ComparisonOperator.EQ)
        ).order_by_field("name").limit(10)
        builder.reset()
        assert builder._conditions.is_empty()
        assert builder._sort_clauses == []
        assert builder._options.limit == 100

    @pytest.mark.asyncio
    async def test_clone(self, builder: MockQueryBuilder) -> None:
        builder.where(QueryCondition(field="id", value=1, operator=ComparisonOperator.EQ))
        clone = builder.clone()
        clone.where(
            QueryCondition(field="name", value="A", operator=ComparisonOperator.EQ)
        )

        assert len(builder._conditions.conditions) == 1
        assert len(clone._conditions.conditions) == 2

    @pytest.mark.asyncio
    async def test_with_specification(self, builder: MockQueryBuilder) -> None:
        class NameIsASpec(Specification[MockModel]):
            def is_satisfied_by(self, candidate: MockModel) -> bool:
                return candidate.name == "A"

        spec = NameIsASpec()
        builder.with_specification(spec)
        assert builder._specification == spec
        
        class ValueIs10Spec(Specification[MockModel]):
            def is_satisfied_by(self, candidate: MockModel) -> bool:
                return candidate.value == 10
                
        spec2 = ValueIs10Spec()
        builder.with_specification(spec2)
        
        assert builder._specification != spec
        assert builder._specification != spec2

    @pytest.mark.asyncio
    async def test_to_dict(self, builder: MockQueryBuilder) -> None:
        builder.where(
            QueryCondition(field="id", value=1, operator=ComparisonOperator.EQ)
        ).order_by_field("name").limit(10)
        data = builder.to_dict()
        assert data["conditions"]["conditions"][0]["field"] == "id"
        assert data["sort"][0]["field"] == "name"
        assert data["options"]["limit"] == 10

    @pytest.mark.asyncio
    async def test_execute(self, builder: MockQueryBuilder) -> None:
        result = await builder.limit(3).execute()
        assert len(result.items) == 3
        assert result.total == 5
        assert result.has_more is True

    @pytest.mark.asyncio
    async def test_first(self, builder: MockQueryBuilder) -> None:
        item = await builder.first()
        assert item is not None
        assert item.id == 1

    @pytest.mark.asyncio
    async def test_count(self, builder: MockQueryBuilder) -> None:
        count = await builder.count()
        assert count == 5
