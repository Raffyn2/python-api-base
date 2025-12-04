"""Application layer for Example system.

Contains DTOs, mappers, use cases for ItemExample and PedidoExample.
Organized by bounded context following DDD principles.

**Feature: example-system-demo**
"""

# Shared
# Item bounded context
from application.examples.item import (
    ItemExampleCreate,
    ItemExampleListResponse,
    ItemExampleMapper,
    ItemExampleResponse,
    ItemExampleUpdate,
    ItemExampleUseCase,
)

# Pedido bounded context
from application.examples.pedido import (
    AddItemRequest,
    CancelPedidoRequest,
    ConfirmPedidoRequest,
    PedidoExampleCreate,
    PedidoExampleMapper,
    PedidoExampleResponse,
    PedidoExampleUpdate,
    PedidoExampleUseCase,
    PedidoItemMapper,
    PedidoItemResponse,
    UpdateStatusRequest,
)
from application.examples.shared import (
    MoneyDTO,
    NotFoundError,
    UseCaseError,
    ValidationError,
)

__all__ = [
    # Shared
    "MoneyDTO",
    "UseCaseError",
    "NotFoundError",
    "ValidationError",
    # Item
    "ItemExampleCreate",
    "ItemExampleUpdate",
    "ItemExampleResponse",
    "ItemExampleListResponse",
    "ItemExampleMapper",
    "ItemExampleUseCase",
    # Pedido
    "PedidoExampleCreate",
    "PedidoExampleUpdate",
    "PedidoExampleResponse",
    "PedidoItemResponse",
    "AddItemRequest",
    "ConfirmPedidoRequest",
    "CancelPedidoRequest",
    "UpdateStatusRequest",
    "PedidoExampleMapper",
    "PedidoItemMapper",
    "PedidoExampleUseCase",
]
