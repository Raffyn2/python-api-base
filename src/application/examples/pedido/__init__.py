"""Application layer for PedidoExample.

Organized into subpackages by responsibility:
- commands/: Pedido commands
- queries/: Pedido queries
- handlers/: Command/Query handlers
- use_cases/: Business logic
- dtos/: Data transfer objects
- mappers/: Entity ↔ DTO mapping

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
    PedidoExampleCreate,
    PedidoExampleResponse,
    PedidoExampleUpdate,
)
from application.examples.pedido.handlers import (
    AddItemToPedidoCommandHandler,
    CancelPedidoCommandHandler,
    ConfirmPedidoCommandHandler,
    CreatePedidoCommandHandler,
    GetPedidoQueryHandler,
    ListPedidosQueryHandler,
)
from application.examples.pedido.mappers import PedidoExampleMapper
from application.examples.pedido.queries import (
    GetPedidoQuery,
    ListPedidosQuery,
)
from application.examples.pedido.use_cases import PedidoExampleUseCase

__all__ = [
    # DTOs
    "AddItemRequest",
    "AddItemToPedidoCommand",
    "AddItemToPedidoCommandHandler",
    "CancelPedidoCommand",
    "CancelPedidoCommandHandler",
    "CancelPedidoRequest",
    "ConfirmPedidoCommand",
    "ConfirmPedidoCommandHandler",
    # Commands
    "CreatePedidoCommand",
    # Handlers
    "CreatePedidoCommandHandler",
    # Queries
    "GetPedidoQuery",
    "GetPedidoQueryHandler",
    "ListPedidosQuery",
    "ListPedidosQueryHandler",
    "PedidoExampleCreate",
    # Mapper
    "PedidoExampleMapper",
    "PedidoExampleResponse",
    "PedidoExampleUpdate",
    # Use Case
    "PedidoExampleUseCase",
]
