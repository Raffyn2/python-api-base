"""Tests for PedidoExample specifications.

Tests specification pattern implementations for order filtering.
"""

from decimal import Decimal

import pytest

from domain.examples.item.entity import Money
from domain.examples.pedido.entity import PedidoExample, PedidoStatus
from domain.examples.pedido.specifications import (
    PedidoConfirmedSpec,
    PedidoCustomerSpec,
    PedidoHasItemsSpec,
    PedidoMinItemsSpec,
    PedidoMinValueSpec,
    PedidoPendingSpec,
    PedidoTenantSpec,
    bulk_orders,
    customer_high_value_orders,
    high_value_pending_orders,
    multi_tenant_query,
    orders_ready_for_processing,
    processable_bulk_orders,
    processable_high_value_orders,
    urgent_orders,
    vip_customer_orders,
)


@pytest.fixture
def pending_pedido() -> PedidoExample:
    """Create a pending order with items."""
    pedido = PedidoExample.create(
        customer_id="cust-123",
        customer_name="John Doe",
        tenant_id="tenant-abc",
    )
    pedido.add_item(
        item_id="item-1",
        item_name="Widget",
        quantity=5,
        unit_price=Money(Decimal("100.00")),
    )
    return pedido


@pytest.fixture
def confirmed_pedido() -> PedidoExample:
    """Create a confirmed order with items."""
    pedido = PedidoExample.create(
        customer_id="cust-456",
        customer_name="Jane Doe",
        tenant_id="tenant-xyz",
    )
    pedido.add_item(
        item_id="item-1",
        item_name="Widget",
        quantity=10,
        unit_price=Money(Decimal("200.00")),
    )
    pedido.confirm()
    return pedido


class TestPedidoPendingSpec:
    """Tests for PedidoPendingSpec."""

    def test_pending_order_satisfies(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoPendingSpec()
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_confirmed_order_not_satisfies(self, confirmed_pedido: PedidoExample) -> None:
        spec = PedidoPendingSpec()
        assert spec.is_satisfied_by(confirmed_pedido) is False


class TestPedidoConfirmedSpec:
    """Tests for PedidoConfirmedSpec."""

    def test_confirmed_order_satisfies(self, confirmed_pedido: PedidoExample) -> None:
        spec = PedidoConfirmedSpec()
        assert spec.is_satisfied_by(confirmed_pedido) is True

    def test_pending_order_not_satisfies(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoConfirmedSpec()
        assert spec.is_satisfied_by(pending_pedido) is False


class TestPedidoMinValueSpec:
    """Tests for PedidoMinValueSpec."""

    def test_order_above_min_value(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoMinValueSpec(Decimal("400.00"))
        # Order total is 500 (5 * 100)
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_order_below_min_value(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoMinValueSpec(Decimal("600.00"))
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_order_equal_min_value(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoMinValueSpec(Decimal("500.00"))
        assert spec.is_satisfied_by(pending_pedido) is True


class TestPedidoCustomerSpec:
    """Tests for PedidoCustomerSpec."""

    def test_matching_customer(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoCustomerSpec("cust-123")
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_non_matching_customer(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoCustomerSpec("cust-999")
        assert spec.is_satisfied_by(pending_pedido) is False


class TestPedidoHasItemsSpec:
    """Tests for PedidoHasItemsSpec."""

    def test_order_with_items(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoHasItemsSpec()
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_empty_order(self) -> None:
        pedido = PedidoExample.create(
            customer_id="cust-123",
            customer_name="John Doe",
        )
        spec = PedidoHasItemsSpec()
        assert spec.is_satisfied_by(pedido) is False


class TestPedidoMinItemsSpec:
    """Tests for PedidoMinItemsSpec."""

    def test_order_above_min_items(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoMinItemsSpec(3)
        # Order has 5 items
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_order_below_min_items(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoMinItemsSpec(10)
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_order_equal_min_items(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoMinItemsSpec(5)
        assert spec.is_satisfied_by(pending_pedido) is True


class TestPedidoTenantSpec:
    """Tests for PedidoTenantSpec."""

    def test_matching_tenant(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoTenantSpec("tenant-abc")
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_non_matching_tenant(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoTenantSpec("tenant-xyz")
        assert spec.is_satisfied_by(pending_pedido) is False


class TestCompositeSpecifications:
    """Tests for composite specification functions."""

    def test_high_value_pending_orders(self, pending_pedido: PedidoExample) -> None:
        spec = high_value_pending_orders(Decimal("400.00"))
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_high_value_pending_orders_not_pending(
        self, confirmed_pedido: PedidoExample
    ) -> None:
        spec = high_value_pending_orders(Decimal("100.00"))
        assert spec.is_satisfied_by(confirmed_pedido) is False

    def test_orders_ready_for_processing(self, confirmed_pedido: PedidoExample) -> None:
        spec = orders_ready_for_processing()
        assert spec.is_satisfied_by(confirmed_pedido) is True

    def test_orders_ready_for_processing_pending(
        self, pending_pedido: PedidoExample
    ) -> None:
        spec = orders_ready_for_processing()
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_vip_customer_orders(self, confirmed_pedido: PedidoExample) -> None:
        spec = vip_customer_orders("cust-456", Decimal("1000.00"))
        # Order total is 2000 (10 * 200)
        assert spec.is_satisfied_by(confirmed_pedido) is True

    def test_vip_customer_orders_wrong_customer(
        self, confirmed_pedido: PedidoExample
    ) -> None:
        spec = vip_customer_orders("cust-999", Decimal("1000.00"))
        assert spec.is_satisfied_by(confirmed_pedido) is False

    def test_bulk_orders(self, confirmed_pedido: PedidoExample) -> None:
        spec = bulk_orders(min_items=5)
        # Order has 10 items
        assert spec.is_satisfied_by(confirmed_pedido) is True

    def test_bulk_orders_not_enough_items(self, pending_pedido: PedidoExample) -> None:
        spec = bulk_orders(min_items=10)
        # Order has 5 items
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_processable_high_value_orders(
        self, confirmed_pedido: PedidoExample
    ) -> None:
        spec = processable_high_value_orders(Decimal("1000.00"))
        assert spec.is_satisfied_by(confirmed_pedido) is True

    def test_processable_high_value_orders_pending(
        self, pending_pedido: PedidoExample
    ) -> None:
        spec = processable_high_value_orders(Decimal("100.00"))
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_multi_tenant_query_pending(self, pending_pedido: PedidoExample) -> None:
        spec = multi_tenant_query("tenant-abc", PedidoStatus.PENDING)
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_multi_tenant_query_confirmed(
        self, confirmed_pedido: PedidoExample
    ) -> None:
        spec = multi_tenant_query("tenant-xyz", PedidoStatus.CONFIRMED)
        assert spec.is_satisfied_by(confirmed_pedido) is True

    def test_multi_tenant_query_wrong_tenant(
        self, pending_pedido: PedidoExample
    ) -> None:
        spec = multi_tenant_query("tenant-wrong", PedidoStatus.PENDING)
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_multi_tenant_query_wrong_status(
        self, confirmed_pedido: PedidoExample
    ) -> None:
        # Test with wrong status
        spec = multi_tenant_query("tenant-xyz", PedidoStatus.PENDING)
        assert spec.is_satisfied_by(confirmed_pedido) is False

    def test_urgent_orders(self, pending_pedido: PedidoExample) -> None:
        spec = urgent_orders(min_items=3)
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_urgent_orders_not_pending(self, confirmed_pedido: PedidoExample) -> None:
        spec = urgent_orders(min_items=5)
        assert spec.is_satisfied_by(confirmed_pedido) is False

    def test_customer_high_value_orders(self, pending_pedido: PedidoExample) -> None:
        spec = customer_high_value_orders("cust-123", Decimal("400.00"))
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_customer_high_value_orders_low_value(
        self, pending_pedido: PedidoExample
    ) -> None:
        spec = customer_high_value_orders("cust-123", Decimal("1000.00"))
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_processable_bulk_orders(self, confirmed_pedido: PedidoExample) -> None:
        spec = processable_bulk_orders(min_items=5)
        assert spec.is_satisfied_by(confirmed_pedido) is True

    def test_processable_bulk_orders_not_confirmed(
        self, pending_pedido: PedidoExample
    ) -> None:
        spec = processable_bulk_orders(min_items=3)
        assert spec.is_satisfied_by(pending_pedido) is False


class TestSpecificationOperators:
    """Tests for specification operators (AND, OR, NOT)."""

    def test_and_operator(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoPendingSpec() & PedidoCustomerSpec("cust-123")
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_and_operator_one_fails(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoPendingSpec() & PedidoCustomerSpec("cust-999")
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_or_operator(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoPendingSpec() | PedidoConfirmedSpec()
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_or_operator_both_fail(self, pending_pedido: PedidoExample) -> None:
        spec = PedidoConfirmedSpec() | PedidoMinValueSpec(Decimal("10000.00"))
        assert spec.is_satisfied_by(pending_pedido) is False

    def test_not_operator(self, pending_pedido: PedidoExample) -> None:
        spec = ~PedidoConfirmedSpec()
        assert spec.is_satisfied_by(pending_pedido) is True

    def test_not_operator_negates(self, confirmed_pedido: PedidoExample) -> None:
        spec = ~PedidoConfirmedSpec()
        assert spec.is_satisfied_by(confirmed_pedido) is False

    def test_complex_composition(self, pending_pedido: PedidoExample) -> None:
        # (Pending AND HasItems) OR (Confirmed AND MinValue)
        spec = (PedidoPendingSpec() & PedidoHasItemsSpec()) | (
            PedidoConfirmedSpec() & PedidoMinValueSpec(Decimal("1000.00"))
        )
        assert spec.is_satisfied_by(pending_pedido) is True
