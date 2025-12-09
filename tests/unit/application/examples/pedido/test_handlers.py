"""Unit tests for pedido example handlers.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 8.2, 8.3**
"""

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from application.examples.pedido.commands import (
    CreatePedidoCommand,
    AddItemToPedidoCommand,
    ConfirmPedidoCommand,
    CancelPedidoCommand,
)
from application.examples.pedido.handlers import (
    CreatePedidoCommandHandler,
    GetPedidoQueryHandler,
    ListPedidosQueryHandler,
)
from application.examples.pedido.queries import GetPedidoQuery, ListPedidosQuery
from domain.examples.item.entity import ItemExample, Money
from domain.examples.pedido.entity import PedidoExample, PedidoStatus


class MockPedidoRepository:
    """Mock repository for pedido testing."""

    def __init__(self) -> None:
        self._pedidos: dict[str, PedidoExample] = {}

    async def get(self, pedido_id: str) -> PedidoExample | None:
        return self._pedidos.get(pedido_id)

    async def create(self, entity: PedidoExample) -> PedidoExample:
        self._pedidos[entity.id] = entity
        return entity

    async def update(self, entity: PedidoExample) -> PedidoExample:
        self._pedidos[entity.id] = entity
        return entity

    async def get_all(self, **kwargs: Any) -> list[PedidoExample]:
        return list(self._pedidos.values())

    async def count(self, **kwargs: Any) -> int:
        return len(self._pedidos)

    def add_pedido(self, pedido: PedidoExample) -> None:
        """Helper to add pedido directly for testing."""
        self._pedidos[pedido.id] = pedido


class MockItemRepository:
    """Mock repository for item testing."""

    def __init__(self) -> None:
        self._items: dict[str, ItemExample] = {}

    async def get(self, item_id: str) -> ItemExample | None:
        return self._items.get(item_id)

    def add_item(self, item: ItemExample) -> None:
        """Helper to add item directly for testing."""
        self._items[item.id] = item


class TestGetPedidoQueryHandler:
    """Tests for GetPedidoQueryHandler."""

    @pytest.fixture
    def repository(self) -> MockPedidoRepository:
        """Create mock repository."""
        return MockPedidoRepository()

    @pytest.fixture
    def handler(self, repository: MockPedidoRepository) -> GetPedidoQueryHandler:
        """Create handler with mock repository."""
        return GetPedidoQueryHandler(repository=repository)

    @pytest.fixture
    def existing_pedido(self, repository: MockPedidoRepository) -> PedidoExample:
        """Create existing pedido in repository."""
        pedido = PedidoExample.create(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
        )
        repository.add_pedido(pedido)
        return pedido

    @pytest.mark.asyncio
    async def test_get_pedido_success(
        self,
        handler: GetPedidoQueryHandler,
        existing_pedido: PedidoExample,
    ) -> None:
        """Test successful pedido retrieval."""
        query = GetPedidoQuery(pedido_id=existing_pedido.id)

        result = await handler.handle(query)

        assert result.is_ok()
        response = result.unwrap()
        assert response.customer_name == "Test Customer"


    @pytest.mark.asyncio
    async def test_get_nonexistent_pedido_fails(
        self, handler: GetPedidoQueryHandler
    ) -> None:
        """Test getting non-existent pedido fails."""
        query = GetPedidoQuery(pedido_id="nonexistent-id")

        result = await handler.handle(query)

        assert result.is_err()


class TestListPedidosQueryHandler:
    """Tests for ListPedidosQueryHandler."""

    @pytest.fixture
    def repository(self) -> MockPedidoRepository:
        """Create mock repository."""
        return MockPedidoRepository()

    @pytest.fixture
    def handler(self, repository: MockPedidoRepository) -> ListPedidosQueryHandler:
        """Create handler with mock repository."""
        return ListPedidosQueryHandler(repository=repository)

    @pytest.mark.asyncio
    async def test_list_pedidos_empty(self, handler: ListPedidosQueryHandler) -> None:
        """Test listing pedidos when empty."""
        query = ListPedidosQuery(page=1, size=10)

        result = await handler.handle(query)

        assert result.is_ok()
        response = result.unwrap()
        assert response.total == 0
        assert len(response.items) == 0

    @pytest.mark.asyncio
    async def test_list_pedidos_with_data(
        self, handler: ListPedidosQueryHandler, repository: MockPedidoRepository
    ) -> None:
        """Test listing pedidos with data."""
        for i in range(3):
            pedido = PedidoExample.create(
                customer_id=f"cust-{i:03d}",
                customer_name=f"Customer {i}",
                customer_email=f"customer{i}@example.com",
            )
            repository.add_pedido(pedido)

        query = ListPedidosQuery(page=1, size=10)

        result = await handler.handle(query)

        assert result.is_ok()
        response = result.unwrap()
        assert response.total == 3
        assert len(response.items) == 3
