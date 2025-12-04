"""GraphQL Types for Examples.

**Feature: interface-modules-workflow-analysis**
"""

from .item_types import (
    ItemConnection,
    ItemCreateInput,
    ItemEdge,
    ItemExampleType,
    ItemMutationResult,
    ItemUpdateInput,
)
from .pedido_types import (
    AddItemToPedidoInput,
    PedidoConnection,
    PedidoCreateInput,
    PedidoEdge,
    PedidoExampleType,
    PedidoItemType,
    PedidoMutationResult,
)
from .shared_types import MutationResult, PageInfoType

__all__ = [
    # Item types
    "ItemExampleType",
    "ItemEdge",
    "ItemConnection",
    "ItemCreateInput",
    "ItemUpdateInput",
    "ItemMutationResult",
    # Pedido types
    "PedidoItemType",
    "PedidoExampleType",
    "PedidoEdge",
    "PedidoConnection",
    "PedidoCreateInput",
    "AddItemToPedidoInput",
    "PedidoMutationResult",
    # Shared
    "PageInfoType",
    "MutationResult",
]
