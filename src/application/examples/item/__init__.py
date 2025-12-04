"""Application layer for ItemExample.

**Feature: application-common-integration**
"""

from application.examples.item.commands import (
    CreateItemCommand,
    DeleteItemCommand,
    UpdateItemCommand,
)
from application.examples.item.dtos import (
    ItemExampleCreate,
    ItemExampleListResponse,
    ItemExampleResponse,
    ItemExampleUpdate,
)
from application.examples.item.handlers import (
    CreateItemCommandHandler,
    DeleteItemCommandHandler,
    GetItemQueryHandler,
    ListItemsQueryHandler,
    UpdateItemCommandHandler,
)
from application.examples.item.mapper import ItemExampleMapper
from application.examples.item.queries import (
    GetItemQuery,
    ListItemsQuery,
)
from application.examples.item.use_case import ItemExampleUseCase

__all__ = [
    # Commands
    "CreateItemCommand",
    # Handlers
    "CreateItemCommandHandler",
    "DeleteItemCommand",
    "DeleteItemCommandHandler",
    # Queries
    "GetItemQuery",
    "GetItemQueryHandler",
    # DTOs
    "ItemExampleCreate",
    "ItemExampleListResponse",
    # Mapper
    "ItemExampleMapper",
    "ItemExampleResponse",
    "ItemExampleUpdate",
    # Use Case (legacy)
    "ItemExampleUseCase",
    "ListItemsQuery",
    "ListItemsQueryHandler",
    "UpdateItemCommand",
    "UpdateItemCommandHandler",
]
