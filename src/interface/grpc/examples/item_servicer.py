"""Example gRPC servicer implementation.

This module provides an example gRPC servicer that demonstrates
integration with domain entities and all RPC patterns.

NOTE: This is example/demo code, not for production use.

**Feature: interface-modules-workflow-analysis**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from grpc import StatusCode
from structlog import get_logger

from interface.grpc.servicers.base import BaseServicer

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from grpc import aio

    from application.common.cqrs import CommandBus, QueryBus

logger = get_logger(__name__)

# Sanitized error messages
_ERR_ITEM_NOT_FOUND = "Item not found"
_ERR_INTERNAL = "Internal error"


@dataclass(slots=True)
class ItemEntity:
    """Demo entity for Item (not production - use domain entities)."""

    id: str
    name: str
    description: str
    sku: str
    quantity: int
    price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ItemServicer(BaseServicer):
    """Example gRPC servicer for Item operations.

    Demonstrates unary, server streaming, client streaming,
    and bidirectional streaming patterns.

    NOTE: Uses in-memory storage for demo purposes.

    **Feature: interface-modules-workflow-analysis**
    """

    def __init__(
        self,
        container: Any | None = None,
        query_bus: QueryBus | None = None,
        command_bus: CommandBus | None = None,
    ) -> None:
        """Initialize item servicer."""
        super().__init__(container, query_bus, command_bus)
        self._items: dict[str, ItemEntity] = {}

    async def GetItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Get a single item by ID (unary RPC)."""
        correlation_id = self._get_correlation_id(context)
        item_id = request.id

        if item_id not in self._items:
            self._logger.warning(
                "item_not_found",
                item_id=item_id,
                correlation_id=correlation_id,
            )
            await context.abort(StatusCode.NOT_FOUND, _ERR_ITEM_NOT_FOUND)
            return None

        return self._entity_to_proto(self._items[item_id])

    async def CreateItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Create a new item (unary RPC)."""
        correlation_id = self._get_correlation_id(context)
        item_id = str(uuid4())
        now = datetime.now(UTC)

        item = ItemEntity(
            id=item_id,
            name=request.name,
            description=request.description,
            sku=request.sku,
            quantity=request.quantity,
            price=request.price,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self._items[item_id] = item
        self._logger.info(
            "item_created",
            item_id=item_id,
            correlation_id=correlation_id,
        )

        return self._entity_to_proto(item)

    async def UpdateItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Update an existing item (unary RPC)."""
        correlation_id = self._get_correlation_id(context)
        item_id = request.id

        if item_id not in self._items:
            self._logger.warning(
                "item_not_found",
                item_id=item_id,
                correlation_id=correlation_id,
            )
            await context.abort(StatusCode.NOT_FOUND, _ERR_ITEM_NOT_FOUND)
            return None

        item = self._items[item_id]
        self._update_item_fields(item, request)
        item.updated_at = datetime.now(UTC)

        self._logger.info(
            "item_updated",
            item_id=item_id,
            correlation_id=correlation_id,
        )

        return self._entity_to_proto(item)

    async def DeleteItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Delete an item (unary RPC)."""
        correlation_id = self._get_correlation_id(context)
        item_id = request.id

        if item_id not in self._items:
            self._logger.warning(
                "item_not_found",
                item_id=item_id,
                correlation_id=correlation_id,
            )
            await context.abort(StatusCode.NOT_FOUND, _ERR_ITEM_NOT_FOUND)
            return None

        del self._items[item_id]
        self._logger.info(
            "item_deleted",
            item_id=item_id,
            correlation_id=correlation_id,
        )

        from google.protobuf.empty_pb2 import Empty

        return Empty()

    async def ListItems(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> AsyncIterator[Any]:
        """List items (server streaming RPC)."""
        correlation_id = self._get_correlation_id(context)
        page_size = min(request.page_size or 10, 100)

        items = list(self._items.values())

        for item in items[:page_size]:
            if context.cancelled():
                self._logger.info(
                    "list_items_cancelled",
                    correlation_id=correlation_id,
                )
                return
            yield self._entity_to_proto(item)

        self._logger.info(
            "list_items_complete",
            count=min(len(items), page_size),
            correlation_id=correlation_id,
        )

    async def BatchCreateItems(
        self,
        request_iterator: AsyncIterator[Any],
        context: aio.ServicerContext,
    ) -> Any:
        """Batch create items (client streaming RPC)."""
        correlation_id = self._get_correlation_id(context)
        created_ids: list[str] = []
        error_count = 0

        async for request in request_iterator:
            try:
                item_id = str(uuid4())
                now = datetime.now(UTC)

                item = ItemEntity(
                    id=item_id,
                    name=request.name,
                    description=request.description,
                    sku=request.sku,
                    quantity=request.quantity,
                    price=request.price,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )

                self._items[item_id] = item
                created_ids.append(item_id)

            except Exception:
                error_count += 1
                self._logger.error(
                    "batch_create_item_error",
                    error_count=error_count,
                    correlation_id=correlation_id,
                )

        self._logger.info(
            "batch_create_complete",
            created_count=len(created_ids),
            error_count=error_count,
            correlation_id=correlation_id,
        )

        return {
            "created_count": len(created_ids),
            "created_ids": created_ids,
            "error_count": error_count,
        }

    async def SyncItems(
        self,
        request_iterator: AsyncIterator[Any],
        context: aio.ServicerContext,
    ) -> AsyncIterator[Any]:
        """Sync items bidirectionally (bidi streaming RPC)."""
        correlation_id = self._get_correlation_id(context)

        async for request in request_iterator:
            if context.cancelled():
                self._logger.info(
                    "sync_items_cancelled",
                    correlation_id=correlation_id,
                )
                return

            request_id = getattr(request, "request_id", "")

            try:
                if hasattr(request, "upsert") and request.HasField("upsert"):
                    item = self._proto_to_entity(request.upsert)
                    self._items[item.id] = item
                    yield {"id": item.id, "success": True, "request_id": request_id}

                elif hasattr(request, "delete_id") and request.HasField("delete_id"):
                    item_id = request.delete_id
                    if item_id in self._items:
                        del self._items[item_id]
                    yield {"id": item_id, "success": True, "request_id": request_id}

            except Exception:
                self._logger.error(
                    "sync_item_error",
                    request_id=request_id,
                    correlation_id=correlation_id,
                )
                yield {
                    "id": "",
                    "success": False,
                    "error": {"code": "ERROR", "message": _ERR_INTERNAL},
                    "request_id": request_id,
                }

    def _update_item_fields(self, item: ItemEntity, request: Any) -> None:
        """Update item fields from request."""
        if hasattr(request, "name") and request.HasField("name"):
            item.name = request.name
        if hasattr(request, "description") and request.HasField("description"):
            item.description = request.description
        if hasattr(request, "quantity") and request.HasField("quantity"):
            item.quantity = request.quantity
        if hasattr(request, "price") and request.HasField("price"):
            item.price = request.price
        if hasattr(request, "is_active") and request.HasField("is_active"):
            item.is_active = request.is_active

    def _entity_to_proto(self, entity: ItemEntity) -> dict[str, Any]:
        """Convert entity to proto message."""
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
            "sku": entity.sku,
            "quantity": entity.quantity,
            "price": entity.price,
            "is_active": entity.is_active,
        }

    def _proto_to_entity(self, proto: Any) -> ItemEntity:
        """Convert proto message to entity."""
        now = datetime.now(UTC)
        return ItemEntity(
            id=proto.id if hasattr(proto, "id") else str(uuid4()),
            name=proto.name,
            description=proto.description,
            sku=proto.sku,
            quantity=proto.quantity,
            price=proto.price,
            is_active=proto.is_active if hasattr(proto, "is_active") else True,
            created_at=now,
            updated_at=now,
        )
