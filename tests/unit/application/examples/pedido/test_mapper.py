"""Unit tests for pedido example mapper.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 8.3**
"""

from decimal import Decimal

import pytest

from application.examples.pedido.mappers.mapper import (
    PedidoExampleMapper,
    PedidoItemMapper,
)
from domain.examples.item.entity import Money
from domain.examples.pedido.entity import PedidoExample


class TestPedidoItemMapper:
    """Tests for PedidoItemMapper class."""

    def test_to_response_converts_item(self) -> None:
        """Test pedido item to response conversion."""
        pedido = PedidoExample.create(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
        )
        pedido.add_item(
            item_id="item-001",
            item_name="Test Item",
            quantity=2,
            unit_price=Money(Decimal("50.00")),
            discount=Decimal("10.00"),
        )

        item = pedido.items[0]
        response = PedidoItemMapper.to_response(item)

        assert response.item_id == "item-001"
        assert response.item_name == "Test Item"
        assert response.quantity == 2
        assert response.unit_price.amount == Decimal("50.00")
        assert response.discount == Decimal("10.00")


class TestPedidoExampleMapper:
    """Tests for PedidoExampleMapper class."""

    @pytest.fixture
    def mapper(self) -> PedidoExampleMapper:
        """Create mapper instance."""
        return PedidoExampleMapper()

    @pytest.fixture
    def sample_pedido(self) -> PedidoExample:
        """Create sample pedido for testing."""
        pedido = PedidoExample.create(
            customer_id="cust-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
            shipping_address="123 Test St",
            notes="Test notes",
            created_by="test_user",
        )
        pedido.add_item(
            item_id="item-001",
            item_name="Test Item",
            quantity=2,
            unit_price=Money(Decimal("50.00")),
        )
        return pedido

    def test_to_dto_converts_pedido(
        self, mapper: PedidoExampleMapper, sample_pedido: PedidoExample
    ) -> None:
        """Test pedido to DTO conversion."""
        dto = mapper.to_dto(sample_pedido)

        assert dto.id == sample_pedido.id
        assert dto.customer_id == sample_pedido.customer_id
        assert dto.customer_name == sample_pedido.customer_name
        assert dto.customer_email == sample_pedido.customer_email
        assert dto.shipping_address == sample_pedido.shipping_address
        assert dto.notes == sample_pedido.notes
        assert dto.items_count == 2  # quantity is 2
        assert len(dto.items) == 1  # 1 line item

    def test_to_dto_list_converts_multiple(
        self, mapper: PedidoExampleMapper
    ) -> None:
        """Test batch pedido to DTO conversion."""
        pedidos = [
            PedidoExample.create(
                customer_id=f"cust-{i:03d}",
                customer_name=f"Customer {i}",
                customer_email=f"customer{i}@example.com",
            )
            for i in range(3)
        ]

        dtos = mapper.to_dto_list(pedidos)

        assert len(dtos) == 3
        for i, dto in enumerate(dtos):
            assert dto.customer_name == f"Customer {i}"

    def test_static_to_response_method(
        self, sample_pedido: PedidoExample
    ) -> None:
        """Test backward compatible static method."""
        dto = PedidoExampleMapper.to_response(sample_pedido)

        assert dto.id == sample_pedido.id
        assert dto.customer_name == sample_pedido.customer_name

    def test_static_to_response_list_method(self) -> None:
        """Test backward compatible static list method."""
        pedidos = [
            PedidoExample.create(
                customer_id=f"cust-{i:03d}",
                customer_name=f"Customer {i}",
                customer_email=f"customer{i}@example.com",
            )
            for i in range(2)
        ]

        dtos = PedidoExampleMapper.to_response_list(pedidos)

        assert len(dtos) == 2
