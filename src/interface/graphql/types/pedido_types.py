"""GraphQL types for PedidoExample.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.1, 3.2, 3.3**
"""

from datetime import datetime

import strawberry

from interface.graphql.types.shared_types import PageInfoType


@strawberry.type
class PedidoItemType:
    """GraphQL type for items in a Pedido."""

    item_id: str
    quantity: int
    unit_price: float


@strawberry.type
class PedidoExampleType:
    """GraphQL type for PedidoExample."""

    id: str
    customer_id: str
    status: str
    items: list[PedidoItemType]
    total: float
    created_at: datetime
    confirmed_at: datetime | None
    cancelled_at: datetime | None


@strawberry.type
class PedidoEdge:
    """Edge type for Pedido connection."""

    node: PedidoExampleType
    cursor: str


@strawberry.type
class PedidoConnection:
    """Relay-style connection for Pedidos."""

    edges: list[PedidoEdge]
    page_info: PageInfoType
    total_count: int


@strawberry.input
class PedidoCreateInput:
    """Input for creating a Pedido."""

    customer_id: str
    customer_name: str
    customer_email: str
    shipping_address: str | None = None
    notes: str | None = None


@strawberry.input
class AddItemToPedidoInput:
    """Input for adding item to Pedido."""

    item_id: str
    quantity: int


@strawberry.type
class PedidoMutationResult:
    """Result of Pedido mutation."""

    success: bool
    pedido: PedidoExampleType | None = None
    error: str | None = None
