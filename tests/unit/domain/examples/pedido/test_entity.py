"""Tests for PedidoExample entity.

Tests aggregate root, order items, status transitions, and domain events.
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


class TestPedidoStatus:
    """Tests for PedidoStatus enum."""

    def test_all_statuses_exist(self) -> None:
        assert PedidoStatus.PENDING.value == "pending"
        assert PedidoStatus.CONFIRMED.value == "confirmed"
        assert PedidoStatus.PROCESSING.value == "processing"
        assert PedidoStatus.SHIPPED.value == "shipped"
        assert PedidoStatus.DELIVERED.value == "delivered"
        assert PedidoStatus.CANCELLED.value == "cancelled"


class TestPedidoItemExample:
    """Tests for PedidoItemExample entity."""

    def test_create_item(self) -> None:
        item = PedidoItemExample.create(
            pedido_id="pedido-1",
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50.00")),
        )
        assert item.pedido_id == "pedido-1"
        assert item.item_id == "item-1"
        assert item.item_name == "Widget"
        assert item.quantity == 2
        assert item.unit_price.amount == Decimal("50.00")
        assert item.discount == Decimal("0")

    def test_create_item_with_discount(self) -> None:
        item = PedidoItemExample.create(
            pedido_id="pedido-1",
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("100.00")),
            discount=Decimal("10"),
        )
        assert item.discount == Decimal("10")

    def test_create_item_invalid_quantity(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be positive"):
            PedidoItemExample.create(
                pedido_id="pedido-1",
                item_id="item-1",
                item_name="Widget",
                quantity=0,
                unit_price=Money(Decimal("50.00")),
            )

    def test_create_item_negative_quantity(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be positive"):
            PedidoItemExample.create(
                pedido_id="pedido-1",
                item_id="item-1",
                item_name="Widget",
                quantity=-1,
                unit_price=Money(Decimal("50.00")),
            )

    def test_create_item_invalid_discount_negative(self) -> None:
        with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
            PedidoItemExample.create(
                pedido_id="pedido-1",
                item_id="item-1",
                item_name="Widget",
                quantity=1,
                unit_price=Money(Decimal("50.00")),
                discount=Decimal("-5"),
            )

    def test_create_item_invalid_discount_over_100(self) -> None:
        with pytest.raises(ValueError, match="Discount must be between 0 and 100"):
            PedidoItemExample.create(
                pedido_id="pedido-1",
                item_id="item-1",
                item_name="Widget",
                quantity=1,
                unit_price=Money(Decimal("50.00")),
                discount=Decimal("101"),
            )

    def test_subtotal_calculation(self) -> None:
        item = PedidoItemExample.create(
            pedido_id="pedido-1",
            item_id="item-1",
            item_name="Widget",
            quantity=3,
            unit_price=Money(Decimal("25.00")),
        )
        assert item.subtotal.amount == Decimal("75.00")

    def test_discount_amount_calculation(self) -> None:
        item = PedidoItemExample.create(
            pedido_id="pedido-1",
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("100.00")),
            discount=Decimal("10"),
        )
        # Subtotal = 200, 10% discount = 20
        assert item.discount_amount.amount == Decimal("20.00")

    def test_total_calculation_with_discount(self) -> None:
        item = PedidoItemExample.create(
            pedido_id="pedido-1",
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("100.00")),
            discount=Decimal("10"),
        )
        # Subtotal = 200, discount = 20, total = 180
        assert item.total.amount == Decimal("180.00")


class TestPedidoExampleCreation:
    """Tests for PedidoExample creation."""

    def test_create_pedido(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
            customer_email="john@example.com",
        )
        assert pedido.customer_id == "cust-123"
        assert pedido.customer_name == "John Doe"
        assert pedido.customer_email == "john@example.com"
        assert pedido.status == PedidoStatus.PENDING
        assert pedido.items == []
        assert pedido.id is not None

    def test_create_pedido_with_shipping_address(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
            shipping_address="123 Main St",
        )
        assert pedido.shipping_address == "123 Main St"

    def test_create_pedido_with_tenant(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
            tenant_id="tenant-abc",
        )
        assert pedido.tenant_id == "tenant-abc"

    def test_create_pedido_emits_event(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        events = pedido.events
        assert len(events) == 1
        assert isinstance(events[0], PedidoCreated)
        assert events[0].customer_id == "cust-123"


class TestPedidoExampleAddItem:
    """Tests for adding items to order."""

    def test_add_item(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        item = pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50.00")),
        )
        assert len(pedido.items) == 1
        assert item.item_name == "Widget"

    def test_add_item_emits_event(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.clear_events()
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50.00")),
        )
        events = pedido.events
        assert len(events) == 1
        assert isinstance(events[0], PedidoItemAdded)

    def test_add_existing_item_increases_quantity(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50.00")),
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=3,
            unit_price=Money(Decimal("50.00")),
        )
        assert len(pedido.items) == 1
        assert pedido.items[0].quantity == 5

    def test_add_item_to_confirmed_order_fails(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50.00")),
        )
        pedido.confirm()
        with pytest.raises(ValueError, match="Cannot add items"):
            pedido.add_item(
                item_id="item-2",
                item_name="Gadget",
                quantity=1,
                unit_price=Money(Decimal("30.00")),
            )


class TestPedidoExampleRemoveItem:
    """Tests for removing items from order."""

    def test_remove_item(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50.00")),
        )
        result = pedido.remove_item("item-1")
        assert result is True
        assert len(pedido.items) == 0

    def test_remove_nonexistent_item(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        result = pedido.remove_item("nonexistent")
        assert result is False

    def test_remove_item_from_confirmed_order_fails(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50.00")),
        )
        pedido.confirm()
        with pytest.raises(ValueError, match="Cannot remove items"):
            pedido.remove_item("item-1")


class TestPedidoExampleStatusTransitions:
    """Tests for order status transitions."""

    @pytest.fixture
    def pedido_with_item(self) -> PedidoExample:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50.00")),
        )
        return pedido

    def test_confirm_order(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.confirm()
        assert pedido_with_item.status == PedidoStatus.CONFIRMED

    def test_confirm_emits_event(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.clear_events()
        pedido_with_item.confirm()
        events = pedido_with_item.events
        assert any(isinstance(e, PedidoCompleted) for e in events)

    def test_confirm_empty_order_fails(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        with pytest.raises(ValueError, match="Cannot confirm order without items"):
            pedido.confirm()

    def test_process_order(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.confirm()
        pedido_with_item.process()
        assert pedido_with_item.status == PedidoStatus.PROCESSING

    def test_process_pending_order_fails(self, pedido_with_item: PedidoExample) -> None:
        with pytest.raises(ValueError, match="Cannot process order"):
            pedido_with_item.process()

    def test_ship_order(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.confirm()
        pedido_with_item.process()
        pedido_with_item.ship()
        assert pedido_with_item.status == PedidoStatus.SHIPPED

    def test_ship_pending_order_fails(self, pedido_with_item: PedidoExample) -> None:
        with pytest.raises(ValueError, match="Cannot ship order"):
            pedido_with_item.ship()

    def test_deliver_order(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.confirm()
        pedido_with_item.process()
        pedido_with_item.ship()
        pedido_with_item.deliver()
        assert pedido_with_item.status == PedidoStatus.DELIVERED

    def test_deliver_pending_order_fails(self, pedido_with_item: PedidoExample) -> None:
        with pytest.raises(ValueError, match="Cannot deliver order"):
            pedido_with_item.deliver()

    def test_cancel_pending_order(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.cancel("Customer request")
        assert pedido_with_item.status == PedidoStatus.CANCELLED

    def test_cancel_emits_event(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.clear_events()
        pedido_with_item.cancel("Customer request")
        events = pedido_with_item.events
        assert any(isinstance(e, PedidoCancelled) for e in events)

    def test_cancel_delivered_order_fails(self, pedido_with_item: PedidoExample) -> None:
        pedido_with_item.confirm()
        pedido_with_item.process()
        pedido_with_item.ship()
        pedido_with_item.deliver()
        with pytest.raises(ValueError, match="Cannot cancel order"):
            pedido_with_item.cancel("Too late")


class TestPedidoExampleCalculations:
    """Tests for order calculations."""

    def test_subtotal(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("50.00")),
        )
        pedido.add_item(
            item_id="item-2",
            item_name="Gadget",
            quantity=1,
            unit_price=Money(Decimal("100.00")),
        )
        assert pedido.subtotal.amount == Decimal("200.00")

    def test_total_with_discount(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=2,
            unit_price=Money(Decimal("100.00")),
            discount=Decimal("10"),
        )
        # Subtotal = 200, discount = 20, total = 180
        assert pedido.total.amount == Decimal("180.00")

    def test_items_count(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=3,
            unit_price=Money(Decimal("50.00")),
        )
        pedido.add_item(
            item_id="item-2",
            item_name="Gadget",
            quantity=2,
            unit_price=Money(Decimal("30.00")),
        )
        assert pedido.items_count == 5

    def test_empty_order_totals(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        assert pedido.subtotal.amount == Decimal("0")
        assert pedido.total.amount == Decimal("0")


class TestPedidoExampleProperties:
    """Tests for order properties."""

    def test_can_be_modified_pending(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        assert pedido.can_be_modified is True

    def test_can_be_modified_confirmed(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50.00")),
        )
        pedido.confirm()
        assert pedido.can_be_modified is False

    def test_can_be_cancelled_pending(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        assert pedido.can_be_cancelled is True

    def test_can_be_cancelled_delivered(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        pedido.add_item(
            item_id="item-1",
            item_name="Widget",
            quantity=1,
            unit_price=Money(Decimal("50.00")),
        )
        pedido.confirm()
        pedido.process()
        pedido.ship()
        pedido.deliver()
        assert pedido.can_be_cancelled is False

    def test_clear_events(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        assert len(pedido.events) > 0
        pedido.clear_events()
        assert len(pedido.events) == 0
