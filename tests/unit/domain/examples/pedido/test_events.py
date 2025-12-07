"""Tests for PedidoExample domain events.

Tests event creation and properties.
"""

from datetime import datetime
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

    def test_create_event(self) -> None:
        event = PedidoCreated(pedido_id="pedido-123", customer_id="cust-456")
        assert event.pedido_id == "pedido-123"
        assert event.customer_id == "cust-456"
        assert event.occurred_at is not None

    def test_event_has_id(self) -> None:
        event = PedidoCreated(pedido_id="pedido-123", customer_id="cust-456")
        assert event.event_id is not None

    def test_occurred_at_is_datetime(self) -> None:
        event = PedidoCreated(pedido_id="pedido-123", customer_id="cust-456")
        assert isinstance(event.occurred_at, datetime)

    def test_event_is_frozen(self) -> None:
        event = PedidoCreated(pedido_id="pedido-123", customer_id="cust-456")
        with pytest.raises(AttributeError):
            event.pedido_id = "changed"  # type: ignore


class TestPedidoItemAdded:
    """Tests for PedidoItemAdded event."""

    def test_create_event(self) -> None:
        event = PedidoItemAdded(
            pedido_id="pedido-123",
            item_id="item-456",
            quantity=5,
            unit_price=Decimal("99.99"),
        )
        assert event.pedido_id == "pedido-123"
        assert event.item_id == "item-456"
        assert event.quantity == 5
        assert event.unit_price == Decimal("99.99")

    def test_event_has_id(self) -> None:
        event = PedidoItemAdded(
            pedido_id="pedido-123",
            item_id="item-456",
            quantity=1,
            unit_price=Decimal("10.00"),
        )
        assert event.event_id is not None

    def test_event_is_frozen(self) -> None:
        event = PedidoItemAdded(
            pedido_id="pedido-123",
            item_id="item-456",
            quantity=1,
            unit_price=Decimal("10.00"),
        )
        with pytest.raises(AttributeError):
            event.quantity = 10  # type: ignore


class TestPedidoCompleted:
    """Tests for PedidoCompleted event."""

    def test_create_event(self) -> None:
        event = PedidoCompleted(
            pedido_id="pedido-123",
            total=Decimal("500.00"),
            items_count=10,
        )
        assert event.pedido_id == "pedido-123"
        assert event.total == Decimal("500.00")
        assert event.items_count == 10

    def test_event_has_id(self) -> None:
        event = PedidoCompleted(
            pedido_id="pedido-123",
            total=Decimal("100.00"),
            items_count=1,
        )
        assert event.event_id is not None

    def test_event_is_frozen(self) -> None:
        event = PedidoCompleted(
            pedido_id="pedido-123",
            total=Decimal("100.00"),
            items_count=1,
        )
        with pytest.raises(AttributeError):
            event.total = Decimal("200.00")  # type: ignore


class TestPedidoCancelled:
    """Tests for PedidoCancelled event."""

    def test_create_event(self) -> None:
        event = PedidoCancelled(
            pedido_id="pedido-123",
            reason="Customer request",
        )
        assert event.pedido_id == "pedido-123"
        assert event.reason == "Customer request"

    def test_event_has_id(self) -> None:
        event = PedidoCancelled(
            pedido_id="pedido-123",
            reason="Out of stock",
        )
        assert event.event_id is not None

    def test_event_is_frozen(self) -> None:
        event = PedidoCancelled(
            pedido_id="pedido-123",
            reason="Customer request",
        )
        with pytest.raises(AttributeError):
            event.reason = "Changed reason"  # type: ignore

    def test_empty_reason(self) -> None:
        event = PedidoCancelled(
            pedido_id="pedido-123",
            reason="",
        )
        assert event.reason == ""
