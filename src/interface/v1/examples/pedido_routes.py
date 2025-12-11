"""Pedido API routes.

**Feature: example-system-demo**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

import structlog
from fastapi import APIRouter, Depends, Header, Query, Request, status

from application.common.dto import ApiResponse, PaginatedResponse
from application.examples import (
    AddItemRequest,
    CancelPedidoRequest,
    PedidoExampleCreate,
    PedidoExampleResponse,
    PedidoExampleUseCase,
)
from infrastructure.security.rbac import RBACUser
from interface.v1.examples.dependencies import (
    get_pedido_use_case,
    require_write_permission,
)
from interface.v1.examples.error_handling import handle_result_error

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/pedidos",
    response_model=PaginatedResponse[PedidoExampleResponse],
    summary="List all orders",
)
async def list_pedidos(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: str | None = Query(None),
    status: str | None = Query(None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    use_case: PedidoExampleUseCase = Depends(get_pedido_use_case),
) -> PaginatedResponse[PedidoExampleResponse]:
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.list(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        status=status,
        tenant_id=x_tenant_id,
    )
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)

    pedidos = result.unwrap()
    logger.info(
        "pedidos_listed",
        count=len(pedidos),
        page=page,
        tenant_id=x_tenant_id,
        correlation_id=correlation_id,
    )
    return PaginatedResponse(
        items=pedidos,
        total=len(pedidos),
        page=page,
        size=page_size,
    )


@router.post(
    "/pedidos",
    response_model=ApiResponse[PedidoExampleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create order",
    description="Create a new order. Requires WRITE permission.",
)
async def create_pedido(
    request: Request,
    data: PedidoExampleCreate,
    user: RBACUser = Depends(require_write_permission),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    use_case: PedidoExampleUseCase = Depends(get_pedido_use_case),
) -> ApiResponse[PedidoExampleResponse]:
    """Create order with RBAC protection."""
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.create(
        data,
        tenant_id=x_tenant_id,
        created_by=user.id,
    )
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    logger.info(
        "pedido_created",
        user_id=user.id,
        tenant_id=x_tenant_id,
        correlation_id=correlation_id,
    )
    return ApiResponse(data=result.unwrap(), status_code=201)


@router.get(
    "/pedidos/{pedido_id}",
    response_model=ApiResponse[PedidoExampleResponse],
    summary="Get order by ID",
)
async def get_pedido(
    request: Request,
    pedido_id: str,
    use_case: PedidoExampleUseCase = Depends(get_pedido_use_case),
) -> ApiResponse[PedidoExampleResponse]:
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.get(pedido_id)
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    return ApiResponse(data=result.unwrap())


@router.post(
    "/pedidos/{pedido_id}/items",
    response_model=ApiResponse[PedidoExampleResponse],
    summary="Add item to order",
)
async def add_item_to_pedido(
    request: Request,
    pedido_id: str,
    data: AddItemRequest,
    use_case: PedidoExampleUseCase = Depends(get_pedido_use_case),
) -> ApiResponse[PedidoExampleResponse]:
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.add_item(pedido_id, data)
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    logger.info(
        "item_added_to_pedido",
        pedido_id=pedido_id,
        correlation_id=correlation_id,
    )
    return ApiResponse(data=result.unwrap())


@router.post(
    "/pedidos/{pedido_id}/confirm",
    response_model=ApiResponse[PedidoExampleResponse],
    summary="Confirm order",
)
async def confirm_pedido(
    request: Request,
    pedido_id: str,
    x_user_id: str = Header(default="system", alias="X-User-Id"),
    use_case: PedidoExampleUseCase = Depends(get_pedido_use_case),
) -> ApiResponse[PedidoExampleResponse]:
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.confirm(pedido_id, confirmed_by=x_user_id)
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    logger.info(
        "pedido_confirmed",
        pedido_id=pedido_id,
        confirmed_by=x_user_id,
        correlation_id=correlation_id,
    )
    return ApiResponse(data=result.unwrap())


@router.post(
    "/pedidos/{pedido_id}/cancel",
    response_model=ApiResponse[PedidoExampleResponse],
    summary="Cancel order",
)
async def cancel_pedido(
    request: Request,
    pedido_id: str,
    data: CancelPedidoRequest,
    x_user_id: str = Header(default="system", alias="X-User-Id"),
    use_case: PedidoExampleUseCase = Depends(get_pedido_use_case),
) -> ApiResponse[PedidoExampleResponse]:
    correlation_id = getattr(request.state, "correlation_id", None)
    result = await use_case.cancel(
        pedido_id,
        reason=data.reason,
        cancelled_by=x_user_id,
    )
    if result.is_err():
        raise handle_result_error(result.unwrap_err(), correlation_id=correlation_id)
    logger.info(
        "pedido_cancelled",
        pedido_id=pedido_id,
        cancelled_by=x_user_id,
        correlation_id=correlation_id,
    )
    return ApiResponse(data=result.unwrap())
