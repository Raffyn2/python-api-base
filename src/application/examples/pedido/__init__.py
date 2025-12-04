"""Application layer for PedidoExample.

**Feature: application-common-integration**
"""

from application.examples.pedido.commands import (
    AddItemToPedidoCommand,
    CancelPedidoCommand,
    ConfirmPedidoCommand,
    CreatePedidoCommand,
)
from application.examples.pedido.dtos import (
    AddItemRequest,
    CancelPedidoRequest,
    ConfirmPedidoRequest,
    PedidoExampleCreate,
    PedidoExampleResponse,
    PedidoExampleUpdate,
    PedidoItemResponse,
    UpdateStatusRequest,
)
from application.examples.pedido.handlers import (
    AddItemToPedidoCommandHandler,
    CancelPedidoCommandHandler,
    ConfirmPedidoCommandHandler,
    CreatePedidoCommandHandler,
    GetPedidoQueryHandler,
    ListPedidosQueryHandler,
)
from application.examples.pedido.mapper import PedidoExampleMapper, PedidoItemMapper
from application.examples.pedido.queries import (
    GetPedidoQuery,
    ListPedidosQuery,
)
from application.examples.pedido.use_case import PedidoExampleUseCase

__all__ = [
    # DTOs
    "PedidoExampleCreate",
    "PedidoExampleUpdate",
    "PedidoExampleResponse",
    "PedidoItemResponse",
    "AddItemRequest",
    "ConfirmPedidoRequest",
    "CancelPedidoRequest",
    "UpdateStatusRequest",
    # Mappers
    "PedidoExampleMapper",
    "PedidoItemMapper",
    # Use Case (legacy)
    "PedidoExampleUseCase",
    # Commands
    "CreatePedidoCommand",
    "AddItemToPedidoCommand",
    "ConfirmPedidoCommand",
    "CancelPedidoCommand",
    # Queries
    "GetPedidoQuery",
    "ListPedidosQuery",
    # Handlers
    "CreatePedidoCommandHandler",
    "AddItemToPedidoCommandHandler",
    "ConfirmPedidoCommandHandler",
    "CancelPedidoCommandHandler",
    "GetPedidoQueryHandler",
    "ListPedidosQueryHandler",
]
