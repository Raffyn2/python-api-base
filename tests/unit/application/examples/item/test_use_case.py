"""Unit tests for item example use case.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 8.1**
"""

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.examples.item.dtos import (
    ItemExampleCreate,
    ItemExampleUpdate,
)
from application.examples.item.use_cases.use_case import ItemExampleUseCase
from application.examples.shared.dtos import MoneyDTO
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


class TestItemExampleUseCaseCreate:
    """Tests for ItemExampleUseCase.create method."""

    @pytest.fixture()
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture()
    def mock_event_bus(self) -> AsyncMock:
        """Create mock event bus."""
        return AsyncMock()

    @pytest.fixture()
    def mock_cache(self) -> MagicMock:
        """Create mock cache."""
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.delete = AsyncMock()
        return cache

    @pytest.fixture()
    def use_case(
        self,
        repository: MockItemRepository,
        mock_event_bus: AsyncMock,
        mock_cache: MagicMock,
    ) -> ItemExampleUseCase:
        """Create use case with mocks."""
        return ItemExampleUseCase(
            repository=repository,
            event_bus=mock_event_bus,
            cache=mock_cache,
        )

    @pytest.mark.asyncio
    async def test_create_item_success(self, use_case: ItemExampleUseCase) -> None:
        """Test successful item creation."""
        data = ItemExampleCreate(
            name="Test Item",
            sku="TEST-001",
            price=MoneyDTO(amount=Decimal("99.99"), currency="BRL"),
            description="Test description",
            quantity=10,
            category="electronics",
        )

        result = await use_case.create(data, created_by="test_user")

        assert result.is_ok()
        response = result.unwrap()
        assert response.name == "Test Item"
        assert response.sku == "TEST-001"
        assert response.quantity == 10

    @pytest.mark.asyncio
    async def test_create_item_duplicate_sku_fails(
        self, use_case: ItemExampleUseCase, repository: MockItemRepository
    ) -> None:
        """Test creating item with duplicate SKU fails."""
        existing = ItemExample.create(
            name="Existing",
            sku="DUPE-001",
            price=Money(Decimal("50.00")),
            description="Existing item",
        )
        repository.add_item(existing)

        data = ItemExampleCreate(
            name="New Item",
            sku="DUPE-001",
            price=MoneyDTO(amount=Decimal("99.99"), currency="BRL"),
        )

        result = await use_case.create(data)

        assert result.is_err()


class TestItemExampleUseCaseGet:
    """Tests for ItemExampleUseCase.get method."""

    @pytest.fixture()
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture()
    def mock_cache(self) -> MagicMock:
        """Create mock cache."""
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.delete = AsyncMock()
        return cache

    @pytest.fixture()
    def use_case(self, repository: MockItemRepository, mock_cache: MagicMock) -> ItemExampleUseCase:
        """Create use case with mocks."""
        return ItemExampleUseCase(repository=repository, cache=mock_cache)

    @pytest.fixture()
    def existing_item(self, repository: MockItemRepository) -> ItemExample:
        """Create existing item in repository."""
        item = ItemExample.create(
            name="Test Item",
            sku="GET-001",
            price=Money(Decimal("50.00")),
            description="Test item",
        )
        repository.add_item(item)
        return item

    @pytest.mark.asyncio
    async def test_get_item_success(self, use_case: ItemExampleUseCase, existing_item: ItemExample) -> None:
        """Test successful item retrieval."""
        result = await use_case.get(existing_item.id)

        assert result.is_ok()
        response = result.unwrap()
        assert response.name == "Test Item"
        assert response.sku == "GET-001"

    @pytest.mark.asyncio
    async def test_get_nonexistent_item_fails(self, use_case: ItemExampleUseCase) -> None:
        """Test getting non-existent item fails."""
        result = await use_case.get("nonexistent-id")

        assert result.is_err()


class TestItemExampleUseCaseUpdate:
    """Tests for ItemExampleUseCase.update method."""

    @pytest.fixture()
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture()
    def mock_cache(self) -> MagicMock:
        """Create mock cache."""
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.delete = AsyncMock()
        return cache

    @pytest.fixture()
    def use_case(self, repository: MockItemRepository, mock_cache: MagicMock) -> ItemExampleUseCase:
        """Create use case with mocks."""
        return ItemExampleUseCase(repository=repository, cache=mock_cache)

    @pytest.fixture()
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
    async def test_update_item_success(self, use_case: ItemExampleUseCase, existing_item: ItemExample) -> None:
        """Test successful item update."""
        data = ItemExampleUpdate(
            name="Updated Name",
            price=MoneyDTO(amount=Decimal("75.00"), currency="BRL"),
        )

        result = await use_case.update(existing_item.id, data, updated_by="test_user")

        assert result.is_ok()
        response = result.unwrap()
        assert response.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_nonexistent_item_fails(self, use_case: ItemExampleUseCase) -> None:
        """Test updating non-existent item fails."""
        data = ItemExampleUpdate(name="Updated Name")

        result = await use_case.update("nonexistent-id", data)

        assert result.is_err()

    @pytest.mark.asyncio
    async def test_update_quantity(self, use_case: ItemExampleUseCase, existing_item: ItemExample) -> None:
        """Test updating item quantity."""
        data = ItemExampleUpdate(quantity=20)

        result = await use_case.update(existing_item.id, data)

        assert result.is_ok()
        response = result.unwrap()
        assert response.quantity == 20


class TestItemExampleUseCaseDelete:
    """Tests for ItemExampleUseCase.delete method."""

    @pytest.fixture()
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture()
    def mock_cache(self) -> MagicMock:
        """Create mock cache."""
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.delete = AsyncMock()
        return cache

    @pytest.fixture()
    def use_case(self, repository: MockItemRepository, mock_cache: MagicMock) -> ItemExampleUseCase:
        """Create use case with mocks."""
        return ItemExampleUseCase(repository=repository, cache=mock_cache)

    @pytest.fixture()
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
    async def test_delete_item_success(self, use_case: ItemExampleUseCase, existing_item: ItemExample) -> None:
        """Test successful item deletion."""
        result = await use_case.delete(existing_item.id, deleted_by="test_user")

        assert result.is_ok()
        assert result.unwrap() is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_item_fails(self, use_case: ItemExampleUseCase) -> None:
        """Test deleting non-existent item fails."""
        result = await use_case.delete("nonexistent-id")

        assert result.is_err()


class TestItemExampleUseCaseList:
    """Tests for ItemExampleUseCase.list method."""

    @pytest.fixture()
    def repository(self) -> MockItemRepository:
        """Create mock repository."""
        return MockItemRepository()

    @pytest.fixture()
    def use_case(self, repository: MockItemRepository) -> ItemExampleUseCase:
        """Create use case with mocks."""
        return ItemExampleUseCase(repository=repository)

    @pytest.mark.asyncio
    async def test_list_items_empty(self, use_case: ItemExampleUseCase) -> None:
        """Test listing items when empty."""
        result = await use_case.list()

        assert result.is_ok()
        items = result.unwrap()
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_list_items_with_data(self, use_case: ItemExampleUseCase, repository: MockItemRepository) -> None:
        """Test listing items with data."""
        for i in range(3):
            item = ItemExample.create(
                name=f"Item {i}",
                sku=f"LST-{i:03d}",
                price=Money(Decimal("10.00")),
                description=f"Item {i} description",
            )
            repository.add_item(item)

        result = await use_case.list()

        assert result.is_ok()
        items = result.unwrap()
        assert len(items) == 3
