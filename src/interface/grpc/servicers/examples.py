"""Example gRPC servicer implementation.

This module provides an example gRPC servicer that demonstrates
integration with domain entities and all RPC patterns.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from grpc import aio
from structlog import get_logger

from src.interface.grpc.servicers.base import BaseServicer

logger = get_logger(__name__)


@dataclass
class ItemEntity:
    """Domain entity for Item."""
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
    """

    def __init__(self, container: Any | None = None) -> None:
        """Initialize item servicer."""
        super().__init__(container)
        # In-memory storage for demo
        self._items: dict[str, ItemEntity] = {}

    async def GetItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Get a single item by ID (unary RPC).
        
        Args:
            request: GetItemRequest
            context: ServicerContext
            
        Returns:
            Item message
        """
        item_id = request.id
        
        if item_id not in self._items:
            await context.abort(
                aio.StatusCode.NOT_FOUND,
                f"Item {item_id} not found",
            )
            return
        
        item = self._items[item_id]
        return self._entity_to_proto(item)

    async def CreateItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Create a new item (unary RPC).
        
        Args:
            request: CreateItemRequest
            context: ServicerContext
            
        Returns:
            Created Item message
        """
        import uuid
        
        item_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
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
        
        logger.info(
            "item_created",
            item_id=item_id,
            name=item.name,
        )
        
        return self._entity_to_proto(item)

    async def UpdateItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Update an existing item (unary RPC).
        
        Args:
            request: UpdateItemRequest
            context: ServicerContext
            
        Returns:
            Updated Item message
        """
        item_id = request.id
        
        if item_id not in self._items:
            await context.abort(
                aio.StatusCode.NOT_FOUND,
                f"Item {item_id} not found",
            )
            return
        
        item = self._items[item_id]
        
        # Update fields if provided
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
        
        item.updated_at = datetime.utcnow()
        
        logger.info(
            "item_updated",
            item_id=item_id,
        )
        
        return self._entity_to_proto(item)

    async def DeleteItem(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> Any:
        """Delete an item (unary RPC).
        
        Args:
            request: DeleteItemRequest
            context: ServicerContext
            
        Returns:
            Empty message
        """
        item_id = request.id
        
        if item_id not in self._items:
            await context.abort(
                aio.StatusCode.NOT_FOUND,
                f"Item {item_id} not found",
            )
            return
        
        del self._items[item_id]
        
        logger.info(
            "item_deleted",
            item_id=item_id,
        )
        
        # Return empty response
        from google.protobuf.empty_pb2 import Empty
        return Empty()

    async def ListItems(
        self,
        request: Any,
        context: aio.ServicerContext,
    ) -> AsyncIterator[Any]:
        """List items with pagination (server streaming RPC).
        
        Args:
            request: ListItemsRequest
            context: ServicerContext
            
        Yields:
            Item messages
        """
        page_size = request.page_size or 10
        
        items = list(self._items.values())
        
        for i, item in enumerate(items[:page_size]):
            if context.cancelled():
                logger.info("list_items_cancelled")
                return
            
            yield self._entity_to_proto(item)
        
        logger.info(
            "list_items_complete",
            count=min(len(items), page_size),
        )

    async def BatchCreateItems(
        self,
        request_iterator: AsyncIterator[Any],
        context: aio.ServicerContext,
    ) -> Any:
        """Batch create items (client streaming RPC).
        
        Args:
            request_iterator: Stream of CreateItemRequest
            context: ServicerContext
            
        Returns:
            BatchCreateResponse
        """
        import uuid
        
        created_ids: list[str] = []
        errors: list[Any] = []
        
        async for request in request_iterator:
            try:
                item_id = str(uuid.uuid4())
                now = datetime.utcnow()
                
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
                
            except Exception as exc:
                logger.error(
                    "batch_create_error",
                    error=str(exc),
                )
        
        logger.info(
            "batch_create_complete",
            created_count=len(created_ids),
        )
        
        # Return response (simplified)
        return {
            "created_count": len(created_ids),
            "created_ids": created_ids,
            "errors": errors,
        }

    async def SyncItems(
        self,
        request_iterator: AsyncIterator[Any],
        context: aio.ServicerContext,
    ) -> AsyncIterator[Any]:
        """Sync items bidirectionally (bidirectional streaming RPC).
        
        Args:
            request_iterator: Stream of ItemSyncRequest
            context: ServicerContext
            
        Yields:
            ItemSyncResponse messages
        """
        async for request in request_iterator:
            if context.cancelled():
                logger.info("sync_items_cancelled")
                return
            
            try:
                # Handle upsert or delete
                if hasattr(request, "upsert") and request.HasField("upsert"):
                    item_proto = request.upsert
                    item = self._proto_to_entity(item_proto)
                    self._items[item.id] = item
                    
                    yield {
                        "id": item.id,
                        "success": True,
                        "request_id": getattr(request, "request_id", ""),
                    }
                    
                elif hasattr(request, "delete_id") and request.HasField("delete_id"):
                    item_id = request.delete_id
                    if item_id in self._items:
                        del self._items[item_id]
                    
                    yield {
                        "id": item_id,
                        "success": True,
                        "request_id": getattr(request, "request_id", ""),
                    }
                    
            except Exception as exc:
                yield {
                    "id": "",
                    "success": False,
                    "error": {"code": "ERROR", "message": str(exc)},
                    "request_id": getattr(request, "request_id", ""),
                }

    def _entity_to_proto(self, entity: ItemEntity) -> dict[str, Any]:
        """Convert entity to proto message (simplified)."""
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
        """Convert proto message to entity (simplified)."""
        return ItemEntity(
            id=proto.id if hasattr(proto, "id") else str(uuid.uuid4()),
            name=proto.name,
            description=proto.description,
            sku=proto.sku,
            quantity=proto.quantity,
            price=proto.price,
            is_active=proto.is_active if hasattr(proto, "is_active") else True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
