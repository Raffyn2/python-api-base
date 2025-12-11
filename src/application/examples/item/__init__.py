"""Application layer for ItemExample.

Organized into subpackages by responsibility:
- commands/: Item commands
- queries/: Item queries
- handlers/: Command/Query handlers
- use_cases/: Business logic
- dtos/: Data transfer objects
- mappers/: Entity ↔ DTO mapping
- batch/: Batch operations
- export/: Export functionality

**Feature: application-common-integration**
"""

from application.examples.item.batch import (
    BatchCreateRequest,
    BatchUpdateRequest,
    ItemExampleBatchService,
)
from application.examples.item.commands import (
    CreateItemCommand,
    DeleteItemCommand,
    UpdateItemCommand,
)
from application.examples.item.dtos import (
    ItemExampleCreate,
    ItemExampleResponse,
    ItemExampleUpdate,
)
from application.examples.item.export import (
    ExportFormat,
    ExportMetadata,
    ExportResult,
    ImportResult,
    ItemExampleExportService,
    ItemExampleImportService,
)
from application.examples.item.handlers import (
    CreateItemCommandHandler,
    DeleteItemCommandHandler,
    GetItemQueryHandler,
    ListItemsQueryHandler,
    UpdateItemCommandHandler,
)
from application.examples.item.mappers import ItemExampleMapper
from application.examples.item.queries import (
    GetItemQuery,
    ListItemsQuery,
)
from application.examples.item.services import ItemExampleService
from application.examples.item.use_cases import ItemExampleUseCase

__all__ = [
    # Batch
    "BatchCreateRequest",
    "BatchUpdateRequest",
    # Commands
    "CreateItemCommand",
    # Handlers
    "CreateItemCommandHandler",
    "DeleteItemCommand",
    "DeleteItemCommandHandler",
    # Export
    "ExportFormat",
    "ExportMetadata",
    "ExportResult",
    # Queries
    "GetItemQuery",
    "GetItemQueryHandler",
    "ImportResult",
    "ItemExampleBatchService",
    # DTOs
    "ItemExampleCreate",
    "ItemExampleExportService",
    "ItemExampleImportService",
    # Mapper
    "ItemExampleMapper",
    "ItemExampleResponse",
    # Service
    "ItemExampleService",
    "ItemExampleUpdate",
    # Use Case
    "ItemExampleUseCase",
    "ListItemsQuery",
    "ListItemsQueryHandler",
    "UpdateItemCommand",
    "UpdateItemCommandHandler",
]
