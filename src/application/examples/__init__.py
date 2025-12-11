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
    ItemExampleService,
    ItemExampleUpdate,
    ItemExampleUseCase,
    ListItemsQuery,
    ListItemsQueryHandler,
    UpdateItemCommand,
    UpdateItemCommandHandler,
)

# Order bounded context
from application.examples.order import (
    OrderItemInput,
    OrderItemOutput,
    PlaceOrderInput,
    PlaceOrderOutput,
    PlaceOrderUseCase,
)

# Pedido bounded context
from application.examples.pedido import (
    AddItemRequest,
    AddItemToPedidoCommand,
    AddItemToPedidoCommandHandler,
    CancelPedidoCommand,
    CancelPedidoCommandHandler,
    CancelPedidoRequest,
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
    # Pedido DTOs
    "AddItemRequest",
    "AddItemToPedidoCommand",
    "AddItemToPedidoCommandHandler",
    # Item Batch
    "BatchCreateRequest",
    "BatchUpdateRequest",
    "CancelPedidoCommand",
    "CancelPedidoCommandHandler",
    "CancelPedidoRequest",
    "ConfirmPedidoCommand",
    "ConfirmPedidoCommandHandler",
    # Item Commands
    "CreateItemCommand",
    # Item Handlers
    "CreateItemCommandHandler",
    # Pedido Commands
    "CreatePedidoCommand",
    # Pedido Handlers
    "CreatePedidoCommandHandler",
    "DeleteItemCommand",
    "DeleteItemCommandHandler",
    # Item Export
    "ExportFormat",
    "ExportMetadata",
    "ExportResult",
    # Item Queries
    "GetItemQuery",
    "GetItemQueryHandler",
    # Pedido Queries
    "GetPedidoQuery",
    "GetPedidoQueryHandler",
    "ImportResult",
    "ItemExampleBatchService",
    # Item DTOs
    "ItemExampleCreate",
    "ItemExampleExportService",
    "ItemExampleImportService",
    # Item Mapper
    "ItemExampleMapper",
    "ItemExampleResponse",
    # Item Service
    "ItemExampleService",
    "ItemExampleUpdate",
    # Item Use Case
    "ItemExampleUseCase",
    "ListItemsQuery",
    "ListItemsQueryHandler",
    "ListPedidosQuery",
    "ListPedidosQueryHandler",
    # Shared DTOs
    "MoneyDTO",
    # Shared Errors
    "NotFoundError",
    # Order DTOs
    "OrderItemInput",
    "OrderItemOutput",
    "PedidoExampleCreate",
    # Pedido Mapper
    "PedidoExampleMapper",
    "PedidoExampleResponse",
    "PedidoExampleUpdate",
    # Pedido Use Case
    "PedidoExampleUseCase",
    "PlaceOrderInput",
    "PlaceOrderOutput",
    # Order Use Case
    "PlaceOrderUseCase",
    "UpdateItemCommand",
    "UpdateItemCommandHandler",
    "UseCaseError",
    "ValidationError",
]
