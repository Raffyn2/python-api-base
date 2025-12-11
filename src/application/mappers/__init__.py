"""Application mappers for interface layer.

Provides mapping functions for converting DTOs to interface-specific types.

**Feature: interface-modules-workflow-analysis**
"""

from application.mappers.graphql import (
    create_empty_item_connection,
    create_empty_pedido_connection,
    create_item_connection,
    create_pedido_connection,
    map_item_dto_to_type,
    map_pedido_dto_to_type,
    map_pedido_item_to_type,
    parse_cursor_to_page,
)

__all__ = [
    # Item mappers
    "create_empty_item_connection",
    # Pedido mappers
    "create_empty_pedido_connection",
    "create_item_connection",
    "create_pedido_connection",
    "map_item_dto_to_type",
    "map_pedido_dto_to_type",
    "map_pedido_item_to_type",
    # Utilities
    "parse_cursor_to_page",
]
