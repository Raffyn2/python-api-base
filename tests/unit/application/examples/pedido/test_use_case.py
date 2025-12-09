"""Unit tests for pedido example use case.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 8.2**
"""

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.examples.pedido.dtos import (
    AddItemRequest,
    PedidoExampleCreate,
)
from application.examples.pedido.use_cases.use_case import PedidoExampleUseCase
from domain.examples.item.entity import ItemExample, Money
from domain.examples.pedido.entity import PedidoExample


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


class TestPedidoExampleUseCaseCreate:
    """Tests for PedidoExampleUseCase.create method."""

    @pytest.fixture
    def pedido_repo(self) -> MockPedidoRepository:
        """Create mock pedido repository."""
        return MockPedidoRepository()

    @pytest.fixture
    def item_repo(self) -> MockItemRepository:
        """Create mock item repository."""
        return MockItemRepository()

    @pytest.fixture
    def use_case(
        self, pedido_repo: MockPedidoRepository, item_repo: MockItemRepository
    ) -> PedidoExampleUseCase:
        """Create use case with mocks."""
        return PedidoExampleUseCase(
            pedido_repo=pedido_repo,
            item_repo=item_repo,
        )

    @pytest.mark.asyncio
    async def test_create_pedido_success(
        self, use_case: PedidoExampleUseCase
    ) -> None:
        """Test successful pedido creation without items."""
        data = PedidoExampleCreate(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
            shipping_address="123 Test St",
            notes="Test order",
        )

        result = await use_case.create(data, created_by="test_user")

        assert result.is_ok()
        response = result.unwrap()
        assert response.customer_name == "Test Customer"
        assert response.customer_email == "test@example.com"

    @pytest.mark.asyncio
    async def test_create_pedido_with_items(
        self,
        use_case: PedidoExampleUseCase,
        item_repo: MockItemRepository,
    ) -> None:
        """Test creating pedido with items."""
        # Add available item
        item = ItemExample.create(
            name="Test Item",
            sku="TEST-001",
            price=Money(Decimal("50.00")),
            description="Test item",
            quantity=10,
        )
        item_repo.add_item(item)

        data = PedidoExampleCreate(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
            items=[AddItemRequest(item_id=item.id, quantity=2)],
        )

        result = await use_case.create(data)

        assert result.is_ok()
        response = result.unwrap()
        assert response.items_count == 2  # quantity is 2

    @pytest.mark.asyncio
    async def test_create_pedido_item_not_found(
        self, use_case: PedidoExampleUseCase
    ) -> None:
        """Test creating pedido with non-existent item fails."""
        data = PedidoExampleCreate(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
            items=[AddItemRequest(item_id="nonexistent", quantity=1)],
        )

        result = await use_case.create(data)

        assert result.is_err()


class TestPedidoExampleUseCaseGet:
    """Tests for PedidoExampleUseCase.get method."""

    @pytest.fixture
    def pedido_repo(self) -> MockPedidoRepository:
        """Create mock pedido repository."""
        return MockPedidoRepository()

    @pytest.fixture
    def item_repo(self) -> MockItemRepository:
        """Create mock item repository."""
        return MockItemRepository()

    @pytest.fixture
    def use_case(
        self, pedido_repo: MockPedidoRepository, item_repo: MockItemRepository
    ) -> PedidoExampleUseCase:
        """Create use case with mocks."""
        return PedidoExampleUseCase(pedido_repo=pedido_repo, item_repo=item_repo)

    @pytest.fixture
    def existing_pedido(self, pedido_repo: MockPedidoRepository) -> PedidoExample:
        """Create existing pedido in repository."""
        pedido = PedidoExample.create(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
        )
        pedido_repo.add_pedido(pedido)
        return pedido

    @pytest.mark.asyncio
    async def test_get_pedido_success(
        self, use_case: PedidoExampleUseCase, existing_pedido: PedidoExample
    ) -> None:
        """Test successful pedido retrieval."""
        result = await use_case.get(existing_pedido.id)

        assert result.is_ok()
        response = result.unwrap()
        assert response.customer_name == "Test Customer"

    @pytest.mark.asyncio
    async def test_get_nonexistent_pedido_fails(
        self, use_case: PedidoExampleUseCase
    ) -> None:
        """Test getting non-existent pedido fails."""
        result = await use_case.get("nonexistent-id")

        assert result.is_err()


class TestPedidoExampleUseCaseConfirm:
    """Tests for PedidoExampleUseCase.confirm method."""

    @pytest.fixture
    def pedido_repo(self) -> MockPedidoRepository:
        """Create mock pedido repository."""
        return MockPedidoRepository()

    @pytest.fixture
    def item_repo(self) -> MockItemRepository:
        """Create mock item repository."""
        return MockItemRepository()

    @pytest.fixture
    def use_case(
        self, pedido_repo: MockPedidoRepository, item_repo: MockItemRepository
    ) -> PedidoExampleUseCase:
        """Create use case with mocks."""
        return PedidoExampleUseCase(pedido_repo=pedido_repo, item_repo=item_repo)

    @pytest.fixture
    def existing_pedido(
        self, pedido_repo: MockPedidoRepository, item_repo: MockItemRepository
    ) -> PedidoExample:
        """Create existing pedido with items in repository."""
        # Add item first
        item = ItemExample.create(
            name="Test Item",
            sku="TEST-001",
            price=Money(Decimal("50.00")),
            description="Test item",
            quantity=10,
        )
        item_repo.add_item(item)

        # Create pedido with item
        pedido = PedidoExample.create(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
        )
        pedido.add_item(
            item_id=item.id,
            item_name=item.name,
            quantity=2,
            unit_price=item.price,
        )
        pedido_repo.add_pedido(pedido)
        return pedido

    @pytest.mark.asyncio
    async def test_confirm_pedido_success(
        self, use_case: PedidoExampleUseCase, existing_pedido: PedidoExample
    ) -> None:
        """Test successful pedido confirmation."""
        result = await use_case.confirm(existing_pedido.id, confirmed_by="test_user")

        assert result.is_ok()
        response = result.unwrap()
        assert response.status == "confirmed"

    @pytest.mark.asyncio
    async def test_confirm_nonexistent_pedido_fails(
        self, use_case: PedidoExampleUseCase
    ) -> None:
        """Test confirming non-existent pedido fails."""
        result = await use_case.confirm("nonexistent-id")

        assert result.is_err()


class TestPedidoExampleUseCaseCancel:
    """Tests for PedidoExampleUseCase.cancel method."""

    @pytest.fixture
    def pedido_repo(self) -> MockPedidoRepository:
        """Create mock pedido repository."""
        return MockPedidoRepository()

    @pytest.fixture
    def item_repo(self) -> MockItemRepository:
        """Create mock item repository."""
        return MockItemRepository()

    @pytest.fixture
    def use_case(
        self, pedido_repo: MockPedidoRepository, item_repo: MockItemRepository
    ) -> PedidoExampleUseCase:
        """Create use case with mocks."""
        return PedidoExampleUseCase(pedido_repo=pedido_repo, item_repo=item_repo)

    @pytest.fixture
    def existing_pedido(self, pedido_repo: MockPedidoRepository) -> PedidoExample:
        """Create existing pedido in repository."""
        pedido = PedidoExample.create(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
        )
        pedido_repo.add_pedido(pedido)
        return pedido

    @pytest.mark.asyncio
    async def test_cancel_pedido_success(
        self, use_case: PedidoExampleUseCase, existing_pedido: PedidoExample
    ) -> None:
        """Test successful pedido cancellation."""
        result = await use_case.cancel(
            existing_pedido.id, reason="Customer request", cancelled_by="test_user"
        )

        assert result.is_ok()
        response = result.unwrap()
        assert response.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_pedido_fails(
        self, use_case: PedidoExampleUseCase
    ) -> None:
        """Test cancelling non-existent pedido fails."""
        result = await use_case.cancel("nonexistent-id", reason="Test")

        assert result.is_err()


class TestPedidoExampleUseCaseList:
    """Tests for PedidoExampleUseCase.list method."""

    @pytest.fixture
    def pedido_repo(self) -> MockPedidoRepository:
        """Create mock pedido repository."""
        return MockPedidoRepository()

    @pytest.fixture
    def item_repo(self) -> MockItemRepository:
        """Create mock item repository."""
        return MockItemRepository()

    @pytest.fixture
    def use_case(
        self, pedido_repo: MockPedidoRepository, item_repo: MockItemRepository
    ) -> PedidoExampleUseCase:
        """Create use case with mocks."""
        return PedidoExampleUseCase(pedido_repo=pedido_repo, item_repo=item_repo)

    @pytest.mark.asyncio
    async def test_list_pedidos_empty(self, use_case: PedidoExampleUseCase) -> None:
        """Test listing pedidos when empty."""
        result = await use_case.list()

        assert result.is_ok()
        pedidos = result.unwrap()
        assert len(pedidos) == 0

    @pytest.mark.asyncio
    async def test_list_pedidos_with_data(
        self, use_case: PedidoExampleUseCase, pedido_repo: MockPedidoRepository
    ) -> None:
        """Test listing pedidos with data."""
        for i in range(3):
            pedido = PedidoExample.create(
                customer_id=f"cust-{i:03d}",
                customer_name=f"Customer {i}",
                customer_email=f"customer{i}@example.com",
            )
            pedido_repo.add_pedido(pedido)

        result = await use_case.list()

        assert result.is_ok()
        pedidos = result.unwrap()
        assert len(pedidos) == 3
