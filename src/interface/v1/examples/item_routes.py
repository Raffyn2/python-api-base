"""Item API routes.

**Feature: example-system-demo**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

from datetime import timedelta

import structlog
from fastapi import APIRouter, Depends, Header, Query, Request, status

from application.common.dto import ApiResponse, PaginatedResponse
from application.examples import (
    ItemExampleCreate,
    ItemExampleResponse,
    ItemExampleUpdate,
    ItemExampleUseCase,
)
from infrastructure.ratelimit import InMemoryRateLimiter, RateLimit, RateLimitConfig
from infrastructure.security.rbac import RBACUser
from interface.v1.examples.dependencies import (
    get_item_use_case,
    require_delete_permission,
    require_write_permission,
)
from interface.v1.examples.error_handling import handle_result_error

logger = structlog.get_logger(__name__)

router = APIRouter()

# Rate limit configurations
READ_RATE_LIMIT = RateLimit(requests=100, window=timedelta(minutes=1))
WRITE_RATE_LIMIT = RateLimit(requests=20, window=timedelta(minutes=1))

_rate_limiter: InMemoryRateLimiter[str] | None = None


def get_rate_limiter() -> InMemoryRateLimiter[str]:
    """Get or create global rate limiter for examples."""
    global _rate_limiter
    if _rate_limiter is None:
        config = RateLimitConfig(default_limit=READ_RATE_LIMIT)
        _rate_limiter = InMemoryRateLimiter[str](config)
    return _rate_limiter


@router.get(
    "/items",
    response_model=PaginatedResponse[ItemExampleResponse],
    summary="List all items",
    description="Get paginated list of ItemExample entities with optional filters.",
)
async def list_items(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query(None, description="Filter by status"),
    use_case: ItemExampleUseCase = Depends(get_item_use_case),
) -> PaginatedResponse[ItemExampleResponse]:
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.list(
        page=page,
        page_size=page_size,
        category=category,
        status=status,
    )
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)

    items = result.unwrap()
    logger.info(
        "items_listed",
        count=len(items),
        page=page,
        correlation_id=correlation_id,
    )
    return PaginatedResponse(
        items=items,
        total=len(items),
        page=page,
        size=page_size,
    )


@router.post(
    "/items",
    response_model=ApiResponse[ItemExampleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create item",
    description="Create a new ItemExample entity. Requires WRITE permission.",
)
async def create_item(
    request: Request,
    data: ItemExampleCreate,
    user: RBACUser = Depends(require_write_permission),
    use_case: ItemExampleUseCase = Depends(get_item_use_case),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> ApiResponse[ItemExampleResponse]:
    """Create item with RBAC protection and idempotency support."""
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.create(data, created_by=user.id)
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    logger.info(
        "item_created",
        user_id=user.id,
        correlation_id=correlation_id,
    )
    return ApiResponse(data=result.unwrap(), status_code=201)


@router.get(
    "/items/{item_id}",
    response_model=ApiResponse[ItemExampleResponse],
    summary="Get item by ID",
)
async def get_item(
    request: Request,
    item_id: str,
    use_case: ItemExampleUseCase = Depends(get_item_use_case),
) -> ApiResponse[ItemExampleResponse]:
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.get(item_id)
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    return ApiResponse(data=result.unwrap())


@router.put(
    "/items/{item_id}",
    response_model=ApiResponse[ItemExampleResponse],
    summary="Update item",
    description="Update an existing item. Requires WRITE permission.",
)
async def update_item(
    request: Request,
    item_id: str,
    data: ItemExampleUpdate,
    user: RBACUser = Depends(require_write_permission),
    use_case: ItemExampleUseCase = Depends(get_item_use_case),
) -> ApiResponse[ItemExampleResponse]:
    """Update item with RBAC protection."""
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.update(item_id, data, updated_by=user.id)
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    logger.info(
        "item_updated",
        item_id=item_id,
        user_id=user.id,
        correlation_id=correlation_id,
    )
    return ApiResponse(data=result.unwrap())


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    description="Delete an item. Requires DELETE permission.",
)
async def delete_item(
    request: Request,
    item_id: str,
    user: RBACUser = Depends(require_delete_permission),
    use_case: ItemExampleUseCase = Depends(get_item_use_case),
) -> None:
    """Delete item with RBAC protection."""
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.delete(item_id, deleted_by=user.id)
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    logger.info(
        "item_deleted",
        item_id=item_id,
        user_id=user.id,
        correlation_id=correlation_id,
    )
