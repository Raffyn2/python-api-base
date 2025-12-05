"""GraphQL mappers for converting DTOs to GraphQL types.

Eliminates duplication by centralizing mapping logic.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.1, 3.2**
"""

from typing import Any

from interface.graphql.types import (
    ItemConnection,
    ItemEdge,
    ItemExampleType,
    PageInfoType,
    PedidoConnection,
    PedidoEdge,
    PedidoExampleType,
    PedidoItemType,
)
from interface.graphql.types.shared_types import create_empty_page_info


def map_item_dto_to_type(item_dto: Any) -> ItemExampleType:
    """Map ItemExampleDTO to GraphQL ItemExampleType."""
    return ItemExampleType(
        id=item_dto.id,
        name=item_dto.name,
        description=item_dto.description or "",
        category=item_dto.category,
        price=float(item_dto.price.amount),
        quantity=item_dto.quantity,
        status=item_dto.status,
        created_at=item_dto.created_at,
        updated_at=item_dto.updated_at,
    )


def map_pedido_item_to_type(item: Any) -> PedidoItemType:
    """Map PedidoItem to GraphQL PedidoItemType."""
    return PedidoItemType(
        item_id=item.item_id,
        quantity=item.quantity,
        unit_price=float(item.unit_price.amount),
    )


def map_pedido_dto_to_type(pedido_dto: Any) -> PedidoExampleType:
    """Map PedidoExampleDTO to GraphQL PedidoExampleType."""
    return PedidoExampleType(
        id=pedido_dto.id,
        customer_id=pedido_dto.customer_id,
        status=pedido_dto.status,
        items=[map_pedido_item_to_type(item) for item in pedido_dto.items],
        total=float(pedido_dto.total.amount),
        created_at=pedido_dto.created_at,
        confirmed_at=pedido_dto.confirmed_at,
        cancelled_at=pedido_dto.cancelled_at,
    )


def _create_page_info(
    edges: list[Any], page: int, page_size: int, total: int
) -> PageInfoType:
    """Create PageInfoType from pagination data (DRY helper)."""
    return PageInfoType(
        has_next_page=(page * page_size) < total,
        has_previous_page=page > 1,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )


def create_item_connection(
    items: list[Any],
    page: int,
    page_size: int,
    total: int,
) -> ItemConnection:
    """Create ItemConnection from paginated items."""
    edges = [
        ItemEdge(
            node=map_item_dto_to_type(item_dto),
            cursor=str((page - 1) * page_size + i),
        )
        for i, item_dto in enumerate(items)
    ]
    return ItemConnection(
        edges=edges,
        page_info=_create_page_info(edges, page, page_size, total),
        total_count=total,
    )


def create_empty_item_connection() -> ItemConnection:
    """Create empty ItemConnection for error cases."""
    return ItemConnection(
        edges=[],
        page_info=create_empty_page_info(),
        total_count=0,
    )


def create_pedido_connection(
    pedidos: list[Any],
    page: int,
    page_size: int,
    total: int,
) -> PedidoConnection:
    """Create PedidoConnection from paginated pedidos."""
    edges = [
        PedidoEdge(
            node=map_pedido_dto_to_type(pedido_dto),
            cursor=str((page - 1) * page_size + i),
        )
        for i, pedido_dto in enumerate(pedidos)
    ]
    return PedidoConnection(
        edges=edges,
        page_info=_create_page_info(edges, page, page_size, total),
        total_count=total,
    )


def create_empty_pedido_connection() -> PedidoConnection:
    """Create empty PedidoConnection for error cases."""
    return PedidoConnection(
        edges=[],
        page_info=create_empty_page_info(),
        total_count=0,
    )


def parse_cursor_to_page(cursor: str | None, page_size: int) -> int:
    """Parse cursor string to page number."""
    if not cursor:
        return 1
    try:
        offset = int(cursor)
        return (offset // page_size) + 1
    except ValueError:
        return 1
