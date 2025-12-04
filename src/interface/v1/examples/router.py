"""API routes for ItemExample and PedidoExample.

**Feature: example-system-demo**
**Feature: infrastructure-examples-integration-fix**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
**Refactored: Split into item_routes.py, pedido_routes.py, dependencies.py**
"""

from fastapi import APIRouter

# Re-export dependencies for backward compatibility
from interface.v1.examples.dependencies import (
    get_current_user_optional,
    get_event_publisher,
    get_item_repository,
    get_item_response_adapter,
    get_item_use_case,
    get_jitter_cache,
    get_pedido_repository,
    get_pedido_response_adapter,
    get_pedido_use_case,
    require_delete_permission,
    require_write_permission,
)
from interface.v1.examples.item_routes import router as item_router
from interface.v1.examples.pedido_routes import router as pedido_router

router = APIRouter(prefix="/examples", tags=["Examples"])

# Include sub-routers
router.include_router(item_router)
router.include_router(pedido_router)

__all__ = [
    "get_current_user_optional",
    "get_event_publisher",
    "get_item_repository",
    "get_item_response_adapter",
    "get_item_use_case",
    "get_jitter_cache",
    "get_pedido_repository",
    "get_pedido_response_adapter",
    "get_pedido_use_case",
    "require_delete_permission",
    "require_write_permission",
    "router",
]
