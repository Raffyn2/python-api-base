"""Unit tests for item example handlers.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 8.1, 8.3**
"""

from decimal import Decimal
from typing import Any

import pytest

from application.examples.item.commands.commands import (
    CreateItemCommand,
    DeleteItemCommand,
    UpdateItemCommand,
)
from application.examples.item.handlers.handlers import (
    CreateItemCommandHandler,
    DeleteItemCommandHandler,
    GetItemQueryHandler,
    ListItemsQueryHandler,
    UpdateItemCommandHandler,
)
from application.examples.item.queries.queries import GetItemQuery, ListItemsQuery
from domain.examples.item.entity import ItemExample, Money


class MockItemRepository:
    """Mock repository for testing."""

    def __init__(self) -> None:
        self._items: dict[str, ItemExample] = {}
        self._by_sku: dict[str, ItemExample] = {}

    async def get(self, item_id: str) -> ItemExample | None:
        return self._items.get(item_id)

    async def get_by_sku(self, sku: str) -> ItemExample | None:
        return self._by_sku.get(sku)

    async def create(self, entity: ItemExample) -> ItemExample:
        self._items[entity.id] = entity
        self._by_sku[entity.sku] = entity
        return entity

    async def update(self, entity: ItemExample) -> ItemExample:
        self._items[entity.id] = entity
        return entity

    async def get_all(self, **kwargs: Any) -> list[ItemExample]:
        return list(self._items.values())

    async def count(self, **kwargs: Any) -> int:
        return len(self._items)

    def add_item(self, item: ItemExample) -> None:
        """Helper to add item directly for testing."""
        self._items[item.id] = item
        self._by_sku[item.sku] = item


class TestCreateItemCommandHandler:
    """Tests for CreateItemCommandHandler."""

    @pytest.fixture
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture
    def handler(self, repository: MockItemRepository) -> CreateItemCommandHandler:
        """Create handler with mock repository."""
        return CreateItemCommandHandler(repository=repository)

    @pytest.mark.asyncio
    async def test_create_item_success(
        self, handler: CreateItemCommandHandler, repository: MockItemRepository
    ) -> None:
        """Test successful item creation."""
        command = CreateItemCommand(
            name="Test Item",
            sku="TEST-001",
            price_amount=Decimal("99.99"),
            price_currency="BRL",
            description="Test description",
            quantity=10,
            category="electronics",
        )

        result = await handler.handle(command)

        assert result.is_ok()
        response = result.unwrap()
        assert response.name == "Test Item"
        assert response.sku == "TEST-001"

    @pytest.mark.asyncio
    async def test_create_item_duplicate_sku_fails(
        self, handler: CreateItemCommandHandler, repository: MockItemRepository
    ) -> None:
        """Test creating item with duplicate SKU fails."""
        existing = ItemExample.create(
            name="Existing",
            sku="DUPE-001",
            price=Money(Decimal("50.00")),
            description="Existing item",
        )
        repository.add_item(existing)

        command = CreateItemCommand(
            name="New Item",
            sku="DUPE-001",
            price_amount=Decimal("99.99"),
        )

        result = await handler.handle(command)

        assert result.is_err()


class TestUpdateItemCommandHandler:
    """Tests for UpdateItemCommandHandler."""

    @pytest.fixture
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture
    def handler(self, repository: MockItemRepository) -> UpdateItemCommandHandler:
        """Create handler with mock repository."""
        return UpdateItemCommandHandler(repository=repository)

    @pytest.fixture
    def existing_item(self, repository: MockItemRepository) -> ItemExample:
        """Create existing item in repository."""
        item = ItemExample.create(
            name="Original Name",
            sku="UPD-001",
            price=Money(Decimal("50.00")),
            description="Original description",
            quantity=5,
        )
        repository.add_item(item)
        return item

    @pytest.mark.asyncio
    async def test_update_item_success(
        self,
        handler: UpdateItemCommandHandler,
        existing_item: ItemExample,
    ) -> None:
        """Test successful item update."""
        command = UpdateItemCommand(
            item_id=existing_item.id,
            name="Updated Name",
            price_amount=Decimal("75.00"),
        )

        result = await handler.handle(command)

        assert result.is_ok()
        response = result.unwrap()
        assert response.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_nonexistent_item_fails(
        self, handler: UpdateItemCommandHandler
    ) -> None:
        """Test updating non-existent item fails."""
        command = UpdateItemCommand(
            item_id="nonexistent-id",
            name="Updated Name",
        )

        result = await handler.handle(command)

        assert result.is_err()


class TestDeleteItemCommandHandler:
    """Tests for DeleteItemCommandHandler."""

    @pytest.fixture
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture
    def handler(self, repository: MockItemRepository) -> DeleteItemCommandHandler:
        """Create handler with mock repository."""
        return DeleteItemCommandHandler(repository=repository)

    @pytest.fixture
    def existing_item(self, repository: MockItemRepository) -> ItemExample:
        """Create existing item in repository."""
        item = ItemExample.create(
            name="To Delete",
            sku="DEL-001",
            price=Money(Decimal("25.00")),
            description="Item to delete",
        )
        repository.add_item(item)
        return item

    @pytest.mark.asyncio
    async def test_delete_item_success(
        self,
        handler: DeleteItemCommandHandler,
        existing_item: ItemExample,
    ) -> None:
        """Test successful item deletion."""
        command = DeleteItemCommand(
            item_id=existing_item.id,
            deleted_by="test_user",
        )

        result = await handler.handle(command)

        assert result.is_ok()
        assert result.unwrap() is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_item_fails(
        self, handler: DeleteItemCommandHandler
    ) -> None:
        """Test deleting non-existent item fails."""
        command = DeleteItemCommand(item_id="nonexistent-id")

        result = await handler.handle(command)

        assert result.is_err()


class TestGetItemQueryHandler:
    """Tests for GetItemQueryHandler."""

    @pytest.fixture
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture
    def handler(self, repository: MockItemRepository) -> GetItemQueryHandler:
        """Create handler with mock repository."""
        return GetItemQueryHandler(repository=repository)

    @pytest.fixture
    def existing_item(self, repository: MockItemRepository) -> ItemExample:
        """Create existing item in repository."""
        item = ItemExample.create(
            name="Query Item",
            sku="QRY-001",
            price=Money(Decimal("30.00")),
            description="Item for query",
        )
        repository.add_item(item)
        return item

    @pytest.mark.asyncio
    async def test_get_item_success(
        self,
        handler: GetItemQueryHandler,
        existing_item: ItemExample,
    ) -> None:
        """Test successful item retrieval."""
        query = GetItemQuery(item_id=existing_item.id)

        result = await handler.handle(query)

        assert result.is_ok()
        response = result.unwrap()
        assert response.name == "Query Item"
        assert response.sku == "QRY-001"

    @pytest.mark.asyncio
    async def test_get_nonexistent_item_fails(
        self, handler: GetItemQueryHandler
    ) -> None:
        """Test getting non-existent item fails."""
        query = GetItemQuery(item_id="nonexistent-id")

        result = await handler.handle(query)

        assert result.is_err()


class TestListItemsQueryHandler:
    """Tests for ListItemsQueryHandler."""

    @pytest.fixture
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture
    def handler(self, repository: MockItemRepository) -> ListItemsQueryHandler:
        """Create handler with mock repository."""
        return ListItemsQueryHandler(repository=repository)

    @pytest.mark.asyncio
    async def test_list_items_empty(self, handler: ListItemsQueryHandler) -> None:
        """Test listing items when empty."""
        query = ListItemsQuery(page=1, size=10)

        result = await handler.handle(query)

        assert result.is_ok()
        response = result.unwrap()
        assert response.total == 0
        assert len(response.items) == 0

    @pytest.mark.asyncio
    async def test_list_items_with_data(
        self, handler: ListItemsQueryHandler, repository: MockItemRepository
    ) -> None:
        """Test listing items with data."""
        for i in range(3):
            item = ItemExample.create(
                name=f"Item {i}",
                sku=f"LST-{i:03d}",
                price=Money(Decimal("10.00")),
                description=f"Item {i} description",
            )
            repository.add_item(item)

        query = ListItemsQuery(page=1, size=10)

        result = await handler.handle(query)

        assert result.is_ok()
        response = result.unwrap()
        assert response.total == 3
        assert len(response.items) == 3
