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
    "AddItemRequest",
    "AddItemToPedidoCommand",
    "AddItemToPedidoCommandHandler",
    "CancelPedidoCommand",
    "CancelPedidoCommandHandler",
    "CancelPedidoRequest",
    "ConfirmPedidoCommand",
    "ConfirmPedidoCommandHandler",
    "ConfirmPedidoRequest",
    # Commands
    "CreatePedidoCommand",
    # Handlers
    "CreatePedidoCommandHandler",
    # Queries
    "GetPedidoQuery",
    "GetPedidoQueryHandler",
    "ListPedidosQuery",
    "ListPedidosQueryHandler",
    # DTOs
    "PedidoExampleCreate",
    # Mappers
    "PedidoExampleMapper",
    "PedidoExampleResponse",
    "PedidoExampleUpdate",
    # Use Case (legacy)
    "PedidoExampleUseCase",
    "PedidoItemMapper",
    "PedidoItemResponse",
    "UpdateStatusRequest",
]
