"""Unit tests for domain/examples/pedido/events.py.

Tests Pedido domain events.

**Task 9.4: Create tests for Pedido domain events**
**Requirements: 2.3**
"""

from decimal import Decimal

import pytest

from domain.examples.pedido.events import (
    PedidoCancelled,
    PedidoCompleted,
    PedidoCreated,
    PedidoItemAdded,
)


class TestPedidoCreated:
    """Tests for PedidoCreated event."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = PedidoCreated(pedido_id="order-123", customer_id="cust-456")

        assert event.pedido_id == "order-123"
        assert event.customer_id == "cust-456"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = PedidoCreated(pedido_id="order-123", customer_id="cust-456")
        assert event.event_type == "pedido.created"

    def test_has_occurred_at(self) -> None:
        """Test event has occurred_at timestamp."""
        event = PedidoCreated(pedido_id="order-123", customer_id="cust-456")
        assert event.occurred_at is not None

    def test_immutability(self) -> None:
        """Test event is immutable."""
        event = PedidoCreated(pedido_id="order-123", customer_id="cust-456")
        with pytest.raises(AttributeError):
            event.pedido_id = "new-id"


class TestPedidoItemAdded:
    """Tests for PedidoItemAdded event."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = PedidoItemAdded(
            pedido_id="order-123",
            item_id="item-456",
            quantity=2,
            unit_price=Decimal("50.00"),
        )

        assert event.pedido_id == "order-123"
        assert event.item_id == "item-456"
        assert event.quantity == 2
        assert event.unit_price == Decimal("50.00")

    def test_event_type(self) -> None:
        """Test event type property."""
        event = PedidoItemAdded(
            pedido_id="order-123",
            item_id="item-456",
            quantity=1,
            unit_price=Decimal("25.00"),
        )
        assert event.event_type == "pedido.item_added"


class TestPedidoCompleted:
    """Tests for PedidoCompleted event."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = PedidoCompleted(
            pedido_id="order-123",
            total=Decimal("150.00"),
            items_count=3,
        )

        assert event.pedido_id == "order-123"
        assert event.total == Decimal("150.00")
        assert event.items_count == 3

    def test_event_type(self) -> None:
        """Test event type property."""
        event = PedidoCompleted(
            pedido_id="order-123",
            total=Decimal("100.00"),
            items_count=2,
        )
        assert event.event_type == "pedido.completed"


class TestPedidoCancelled:
    """Tests for PedidoCancelled event."""

    def test_creation(self) -> None:
        """Test event creation."""
        event = PedidoCancelled(pedido_id="order-123", reason="Customer request")

        assert event.pedido_id == "order-123"
        assert event.reason == "Customer request"

    def test_event_type(self) -> None:
        """Test event type property."""
        event = PedidoCancelled(pedido_id="order-123", reason="")
        assert event.event_type == "pedido.cancelled"
