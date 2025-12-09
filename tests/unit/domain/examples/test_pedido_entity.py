"""Unit tests for domain/examples/pedido/entity.py.

Tests Pedido entity creation and validation.

**Task 9.3: Create tests for Pedido entity**
**Requirements: 2.3**
"""

from decimal import Decimal

import pytest

from domain.examples.item.entity import Money
from domain.examples.pedido.entity import (
    PedidoExample,
    PedidoItemExample,
    PedidoStatus,
)
from domain.examples.pedido.events import (
    PedidoCancelled,
    PedidoCompleted,
    PedidoCreated,
    PedidoItemAdded,
)


class TestPedidoItemExample:
    """Tests for PedidoItemExample."""

    def test_create_item(self) -> None:
        """Test creating order item."""
        item = PedidoItemExample.create(
            pedido_id="order-123",
            item_id="item-456",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50")),
        )

        assert item.pedido_id == "order-123"
        assert item.item_id == "item-456"
        assert item.quantity == 2

    def test_zero_quantity_raises(self) -> None:
        """Test zero quantity raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            PedidoItemExample.create(
                pedido_id="order-123",
                item_id="item-456",
                item_name="Widget",
                quantity=0,
                unit_price=Money(Decimal("50")),
            )

    def test_negative_quantity_raises(self) -> None:
        """Test negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            PedidoItemExample.create(
                pedido_id="order-123",
                item_id="item-456",
                item_name="Widget",
                quantity=-1,
                unit_price=Money(Decimal("50")),
            )

    def test_invalid_discount_raises(self) -> None:
        """Test invalid discount raises ValueError."""
        with pytest.raises(ValueError, match="0 and 100"):
            PedidoItemExample.create(
                pedido_id="order-123",
                item_id="item-456",
                item_name="Widget",
                quantity=1,
                unit_price=Money(Decimal("50")),
                discount=Decimal("101"),
            )


class TestPedidoItemCalculations:
    """Tests for PedidoItemExample calculations."""

    def test_subtotal(self) -> None:
        """Test subtotal calculation."""
        item = PedidoItemExample.create(
            pedido_id="order-123",
            item_id="item-456",
            item_name="Widget",
            quantity=3,
            unit_price=Money(Decimal("25")),
        )

        assert item.subtotal.amount == Decimal("75")

    def test_discount_amount(self) -> None:
        """Test discount amount calculation."""
        item = PedidoItemExample.create(
            pedido_id="order-123",
            item_id="item-456",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("100")),
            discount=Decimal("10"),
        )

        assert item.discount_amount.amount == Decimal("20")

    def test_total_with_discount(self) -> None:
        """Test total calculation with discount."""
        item = PedidoItemExample.create(
            pedido_id="order-123",
            item_id="item-456",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("100")),
            discount=Decimal("10"),
        )

        assert item.total.amount == Decimal("180")


class TestPedidoExampleCreate:
    """Tests for PedidoExample.create factory method."""

    def test_create_order(self) -> None:
        """Test creating an order."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
            customer_email="john@example.com",
        )

        assert order.customer_id == "cust-123"
        assert order.customer_name == "John Doe"
        assert order.status == PedidoStatus.PENDING

    def test_create_emits_event(self) -> None:
        """Test create emits PedidoCreated event."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )

        events = order.events
        assert len(events) == 1
        assert isinstance(events[0], PedidoCreated)


class TestPedidoExampleAddItem:
    """Tests for PedidoExample.add_item method."""

    def test_add_item(self) -> None:
        """Test adding item to order."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.clear_events()

        item = order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50")),
        )

        assert len(order.items) == 1
        assert item.quantity == 2

    def test_add_item_emits_event(self) -> None:
        """Test add_item emits PedidoItemAdded event."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.clear_events()

        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50")),
        )

        events = order.events
        assert len(events) == 1
        assert isinstance(events[0], PedidoItemAdded)

    def test_add_existing_item_increases_quantity(self) -> None:
        """Test adding existing item increases quantity."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )

        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50")),
        )
        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=3,
            unit_price=Money(Decimal("50")),
        )

        assert len(order.items) == 1
        assert order.items[0].quantity == 5

    def test_add_item_to_non_pending_raises(self) -> None:
        """Test adding item to non-pending order raises."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50")),
        )
        order.confirm()

        with pytest.raises(ValueError, match="Cannot add items"):
            order.add_item(
                item_id="item-789",
                item_name="Gadget",
                quantity=1,
                unit_price=Money(Decimal("30")),
            )


class TestPedidoExampleStatusTransitions:
    """Tests for PedidoExample status transitions."""

    def test_confirm(self) -> None:
        """Test confirming order."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50")),
        )

        order.confirm()

        assert order.status == PedidoStatus.CONFIRMED

    def test_confirm_empty_order_raises(self) -> None:
        """Test confirming empty order raises."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )

        with pytest.raises(ValueError, match="without items"):
            order.confirm()

    def test_process(self) -> None:
        """Test processing order."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50")),
        )
        order.confirm()

        order.process()

        assert order.status == PedidoStatus.PROCESSING

    def test_ship(self) -> None:
        """Test shipping order."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50")),
        )
        order.confirm()
        order.process()

        order.ship()

        assert order.status == PedidoStatus.SHIPPED

    def test_deliver(self) -> None:
        """Test delivering order."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50")),
        )
        order.confirm()
        order.process()
        order.ship()

        order.deliver()

        assert order.status == PedidoStatus.DELIVERED

    def test_cancel(self) -> None:
        """Test cancelling order."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.clear_events()

        order.cancel(reason="Customer request")

        assert order.status == PedidoStatus.CANCELLED
        events = order.events
        assert any(isinstance(e, PedidoCancelled) for e in events)

    def test_cancel_delivered_raises(self) -> None:
        """Test cancelling delivered order raises."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-456",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50")),
        )
        order.confirm()
        order.process()
        order.ship()
        order.deliver()

        with pytest.raises(ValueError, match="Cannot cancel"):
            order.cancel(reason="Too late")


class TestPedidoExampleCalculations:
    """Tests for PedidoExample calculations."""

    def test_subtotal(self) -> None:
        """Test subtotal calculation."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50")),
        )
        order.add_item(
            item_id="item-2",
            item_name="Gadget",
            quantity=1,
            unit_price=Money(Decimal("30")),
        )

        assert order.subtotal.amount == Decimal("130")

    def test_total(self) -> None:
        """Test total calculation."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50")),
        )

        assert order.total.amount == Decimal("100")

    def test_items_count(self) -> None:
        """Test items count."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=3,
            unit_price=Money(Decimal("50")),
        )
        order.add_item(
            item_id="item-2",
            item_name="Gadget",
            quantity=2,
            unit_price=Money(Decimal("30")),
        )

        assert order.items_count == 5


class TestPedidoExampleProperties:
    """Tests for PedidoExample properties."""

    def test_can_be_modified_pending(self) -> None:
        """Test can_be_modified is True for pending orders."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )

        assert order.can_be_modified is True

    def test_can_be_modified_confirmed(self) -> None:
        """Test can_be_modified is False for confirmed orders."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        order.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50")),
        )
        order.confirm()

        assert order.can_be_modified is False

    def test_can_be_cancelled(self) -> None:
        """Test can_be_cancelled property."""
        order = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )

        assert order.can_be_cancelled is True
