"""PedidoExample bounded context.

**Feature: example-system-demo**
"""

from domain.examples.pedido.entity import (
    PedidoCancelled,
    PedidoCompleted,
    PedidoCreated,
    PedidoExample,
    PedidoItemAdded,
    PedidoItemExample,
    PedidoStatus,
)
from domain.examples.pedido.specifications import (
    PedidoConfirmedSpec,
    PedidoCustomerSpec,
    PedidoHasItemsSpec,
    PedidoMinItemsSpec,
    PedidoMinValueSpec,
    PedidoPendingSpec,
    PedidoTenantSpec,
    high_value_pending_orders,
    orders_ready_for_processing,
)

__all__ = [
    # Events
    "PedidoCancelled",
    "PedidoCompleted",
    # Specifications
    "PedidoConfirmedSpec",
    "PedidoCreated",
    "PedidoCustomerSpec",
    # Entity
    "PedidoExample",
    "PedidoHasItemsSpec",
    "PedidoItemAdded",
    "PedidoItemExample",
    "PedidoMinItemsSpec",
    "PedidoMinValueSpec",
    "PedidoPendingSpec",
    "PedidoStatus",
    "PedidoTenantSpec",
    "high_value_pending_orders",
    "orders_ready_for_processing",
]
