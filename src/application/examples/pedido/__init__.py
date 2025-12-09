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
    # DTOs
    "PedidoExampleCreate",
    "PedidoExampleUpdate",
    "PedidoExampleResponse",
    # Mapper
    "PedidoExampleMapper",
    # Use Case
    "PedidoExampleUseCase",
]
