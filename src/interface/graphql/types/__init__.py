"""GraphQL Types for Examples.

**Feature: interface-modules-workflow-analysis**
"""

from interface.graphql.types.item_types import (
    ItemConnection,
    ItemCreateInput,
    ItemEdge,
    ItemExampleType,
    ItemMutationResult,
    ItemUpdateInput,
)
from interface.graphql.types.pedido_types import (
    AddItemToPedidoInput,
    PedidoConnection,
    PedidoCreateInput,
    PedidoEdge,
    PedidoExampleType,
    PedidoItemType,
    PedidoMutationResult,
)
from interface.graphql.types.shared_types import MutationResult, PageInfoType

__all__ = [
    "AddItemToPedidoInput",
    "ItemConnection",
    "ItemCreateInput",
    "ItemEdge",
    # Item types
    "ItemExampleType",
    "ItemMutationResult",
    "ItemUpdateInput",
    "MutationResult",
    # Shared
    "PageInfoType",
    "PedidoConnection",
    "PedidoCreateInput",
    "PedidoEdge",
    "PedidoExampleType",
    # Pedido types
    "PedidoItemType",
    "PedidoMutationResult",
]
