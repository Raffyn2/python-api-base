"""Application layer for Example system.

Contains DTOs, mappers, use cases for ItemExample and PedidoExample.
Organized by bounded context following DDD principles.

Structure:
- item/: Item example with commands, queries, handlers, use cases, batch, export
- pedido/: Pedido example with commands, queries, handlers, use cases
- shared/: Shared DTOs and errors

**Feature: example-system-demo**
"""

# Item bounded context
from application.examples.item import (
    BatchCreateRequest,
    BatchUpdateRequest,
    CreateItemCommand,
    CreateItemCommandHandler,
    DeleteItemCommand,
    DeleteItemCommandHandler,
    ExportFormat,
    ExportMetadata,
    ExportResult,
    GetItemQuery,
    GetItemQueryHandler,
    ImportResult,
    ItemExampleBatchService,
    ItemExampleCreate,
    ItemExampleExportService,
    ItemExampleImportService,
    ItemExampleMapper,
    ItemExampleResponse,
    ItemExampleUpdate,
    ItemExampleUseCase,
    ListItemsQuery,
    ListItemsQueryHandler,
    UpdateItemCommand,
    UpdateItemCommandHandler,
)

# Pedido bounded context
from application.examples.pedido import (
    AddItemToPedidoCommand,
    AddItemToPedidoCommandHandler,
    CancelPedidoCommand,
    CancelPedidoCommandHandler,
    ConfirmPedidoCommand,
    ConfirmPedidoCommandHandler,
    CreatePedidoCommand,
    CreatePedidoCommandHandler,
    GetPedidoQuery,
    GetPedidoQueryHandler,
    ListPedidosQuery,
    ListPedidosQueryHandler,
    PedidoExampleCreate,
    PedidoExampleMapper,
    PedidoExampleResponse,
    PedidoExampleUpdate,
    PedidoExampleUseCase,
)

# Shared
from application.examples.shared import (
    MoneyDTO,
    NotFoundError,
    UseCaseError,
    ValidationError,
)

__all__ = [
    # Item Commands
    "CreateItemCommand",
    "UpdateItemCommand",
    "DeleteItemCommand",
    # Item Queries
    "GetItemQuery",
    "ListItemsQuery",
    # Item Handlers
    "CreateItemCommandHandler",
    "UpdateItemCommandHandler",
    "DeleteItemCommandHandler",
    "GetItemQueryHandler",
    "ListItemsQueryHandler",
    # Item DTOs
    "ItemExampleCreate",
    "ItemExampleUpdate",
    "ItemExampleResponse",
    # Item Mapper
    "ItemExampleMapper",
    # Item Batch
    "BatchCreateRequest",
    "BatchUpdateRequest",
    "ItemExampleBatchService",
    # Item Export
    "ExportFormat",
    "ExportMetadata",
    "ExportResult",
    "ImportResult",
    "ItemExampleExportService",
    "ItemExampleImportService",
    # Item Use Case
    "ItemExampleUseCase",
    # Pedido Commands
    "CreatePedidoCommand",
    "AddItemToPedidoCommand",
    "ConfirmPedidoCommand",
    "CancelPedidoCommand",
    # Pedido Queries
    "GetPedidoQuery",
    "ListPedidosQuery",
    # Pedido Handlers
    "CreatePedidoCommandHandler",
    "AddItemToPedidoCommandHandler",
    "ConfirmPedidoCommandHandler",
    "CancelPedidoCommandHandler",
    "GetPedidoQueryHandler",
    "ListPedidosQueryHandler",
    # Pedido DTOs
    "PedidoExampleCreate",
    "PedidoExampleUpdate",
    "PedidoExampleResponse",
    # Pedido Mapper
    "PedidoExampleMapper",
    # Pedido Use Case
    "PedidoExampleUseCase",
    # Shared DTOs
    "MoneyDTO",
    # Shared Errors
    "NotFoundError",
    "UseCaseError",
    "ValidationError",
]
