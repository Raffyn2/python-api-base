"""GraphQL Mutation root for Examples.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.3**
**Improvement: P2-1 - Use CQRS pattern**
"""

from decimal import Decimal

import strawberry
import structlog
from strawberry.types import Info

from application.common.cqrs import CommandBus
from application.examples.item.commands import (
    CreateItemCommand,
    DeleteItemCommand,
    UpdateItemCommand,
)
from application.examples.pedido.commands import (
    ConfirmPedidoCommand,
    CreatePedidoCommand,
)
from application.mappers.graphql import (
    map_item_dto_to_type,
    map_pedido_dto_to_type,
)
from core.base.patterns.result import Err, Ok
from interface.graphql.types import (
    ItemCreateInput,
    ItemMutationResult,
    ItemUpdateInput,
    MutationResult,
    PedidoCreateInput,
    PedidoMutationResult,
)

logger = structlog.get_logger(__name__)

# Sanitized error messages (avoid exposing internals)
_ERR_INTERNAL = "An internal error occurred"
_ERR_NOT_FOUND = "Resource not found"
_ERR_VALIDATION = "Validation failed"


def _get_command_bus(info: Info) -> CommandBus:
    """Extract CommandBus from context.

    Raises:
        RuntimeError: If CommandBus not configured in context.
    """
    bus = info.context.get("command_bus")
    if bus is None:
        logger.error("graphql_context_missing", component="command_bus")
        raise RuntimeError("CommandBus not configured")
    return bus


def _sanitize_error(error: Exception) -> str:
    """Sanitize error message for client response."""
    error_type = type(error).__name__
    if "NotFound" in error_type:
        return _ERR_NOT_FOUND
    if "Validation" in error_type:
        return _ERR_VALIDATION
    return _ERR_INTERNAL


def _get_correlation_id(info: Info) -> str | None:
    """Extract correlation ID from context."""
    return info.context.get("correlation_id")


@strawberry.type
class Mutation:
    """GraphQL Mutation root for Examples."""

    @strawberry.mutation
    async def create_item(self, info: Info, input: ItemCreateInput) -> ItemMutationResult:
        """Create a new item."""
        command_bus = _get_command_bus(info)
        correlation_id = _get_correlation_id(info)

        command = CreateItemCommand(
            name=input.name,
            sku=input.sku,
            price_amount=Decimal(str(input.price)),
            price_currency="BRL",
            description=input.description or "",
            quantity=input.quantity,
            category=input.category,
            correlation_id=correlation_id,
        )

        logger.info(
            "graphql_mutation",
            operation="create_item",
            name=input.name,
            correlation_id=correlation_id,
        )
        result = await command_bus.dispatch(command)

        match result:
            case Ok(item_dto):
                return ItemMutationResult(success=True, item=map_item_dto_to_type(item_dto))
            case Err(error):
                logger.warning(
                    "graphql_mutation_failed",
                    operation="create_item",
                    error_type=type(error).__name__,
                    correlation_id=correlation_id,
                )
                return ItemMutationResult(success=False, error=_sanitize_error(error))

    @strawberry.mutation
    async def update_item(self, info: Info, id: str, input: ItemUpdateInput) -> ItemMutationResult:
        """Update an existing item."""
        command_bus = _get_command_bus(info)
        correlation_id = _get_correlation_id(info)

        command = UpdateItemCommand(
            item_id=id,
            name=input.name,
            description=input.description,
            price_amount=Decimal(str(input.price)) if input.price is not None else None,
            quantity=input.quantity,
            category=input.category,
            correlation_id=correlation_id,
        )

        logger.info(
            "graphql_mutation",
            operation="update_item",
            item_id=id,
            correlation_id=correlation_id,
        )
        result = await command_bus.dispatch(command)

        match result:
            case Ok(item_dto):
                return ItemMutationResult(success=True, item=map_item_dto_to_type(item_dto))
            case Err(error):
                logger.warning(
                    "graphql_mutation_failed",
                    operation="update_item",
                    error_type=type(error).__name__,
                    correlation_id=correlation_id,
                )
                return ItemMutationResult(success=False, error=_sanitize_error(error))

    @strawberry.mutation
    async def delete_item(self, info: Info, id: str) -> MutationResult:
        """Delete an item."""
        command_bus = _get_command_bus(info)
        correlation_id = _get_correlation_id(info)
        command = DeleteItemCommand(item_id=id, correlation_id=correlation_id)

        logger.info(
            "graphql_mutation",
            operation="delete_item",
            item_id=id,
            correlation_id=correlation_id,
        )
        result = await command_bus.dispatch(command)

        match result:
            case Ok(_):
                return MutationResult(success=True, message="Item deleted")
            case Err(error):
                logger.warning(
                    "graphql_mutation_failed",
                    operation="delete_item",
                    error_type=type(error).__name__,
                    correlation_id=correlation_id,
                )
                return MutationResult(success=False, message=_sanitize_error(error))

    @strawberry.mutation
    async def create_pedido(self, info: Info, input: PedidoCreateInput) -> PedidoMutationResult:
        """Create a new pedido."""
        command_bus = _get_command_bus(info)
        correlation_id = _get_correlation_id(info)

        command = CreatePedidoCommand(
            customer_id=input.customer_id,
            customer_name=input.customer_name,
            customer_email=input.customer_email,
            shipping_address=input.shipping_address or "",
            notes=input.notes or "",
            correlation_id=correlation_id,
        )

        logger.info(
            "graphql_mutation",
            operation="create_pedido",
            customer_id=input.customer_id,
            correlation_id=correlation_id,
        )
        result = await command_bus.dispatch(command)

        match result:
            case Ok(pedido_dto):
                return PedidoMutationResult(success=True, pedido=map_pedido_dto_to_type(pedido_dto))
            case Err(error):
                logger.warning(
                    "graphql_mutation_failed",
                    operation="create_pedido",
                    error_type=type(error).__name__,
                    correlation_id=correlation_id,
                )
                return PedidoMutationResult(success=False, error=_sanitize_error(error))

    @strawberry.mutation
    async def confirm_pedido(self, info: Info, id: str) -> PedidoMutationResult:
        """Confirm a pedido."""
        command_bus = _get_command_bus(info)
        correlation_id = _get_correlation_id(info)
        command = ConfirmPedidoCommand(pedido_id=id, correlation_id=correlation_id)

        logger.info(
            "graphql_mutation",
            operation="confirm_pedido",
            pedido_id=id,
            correlation_id=correlation_id,
        )
        result = await command_bus.dispatch(command)

        match result:
            case Ok(pedido_dto):
                return PedidoMutationResult(success=True, pedido=map_pedido_dto_to_type(pedido_dto))
            case Err(error):
                logger.warning(
                    "graphql_mutation_failed",
                    operation="confirm_pedido",
                    error_type=type(error).__name__,
                    correlation_id=correlation_id,
                )
                return PedidoMutationResult(success=False, error=_sanitize_error(error))
