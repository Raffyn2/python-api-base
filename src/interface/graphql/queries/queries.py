"""GraphQL Query root for Examples.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.1, 3.2**
**Improvement: P2-1 - Use CQRS pattern**
"""

import strawberry
import structlog
from strawberry.types import Info

from application.common.cqrs import QueryBus
from application.examples.item.queries import GetItemQuery, ListItemsQuery
from application.examples.pedido.queries import GetPedidoQuery, ListPedidosQuery
from application.mappers.graphql import (
    create_empty_item_connection,
    create_empty_pedido_connection,
    create_item_connection,
    create_pedido_connection,
    map_item_dto_to_type,
    map_pedido_dto_to_type,
    parse_cursor_to_page,
)
from core.base.patterns.result import Err, Ok
from interface.graphql.types import (
    ItemConnection,
    ItemExampleType,
    PedidoConnection,
    PedidoExampleType,
)

logger = structlog.get_logger(__name__)

# Pagination constants
_DEFAULT_PAGE_SIZE = 10
_MIN_PAGE_SIZE = 1
_MAX_PAGE_SIZE = 100


def _get_query_bus(info: Info) -> QueryBus:
    """Extract QueryBus from context.

    Raises:
        RuntimeError: If QueryBus not configured in context.
    """
    bus = info.context.get("query_bus")
    if bus is None:
        logger.error("graphql_context_missing", component="query_bus")
        raise RuntimeError("QueryBus not configured")
    return bus


def _get_correlation_id(info: Info) -> str | None:
    """Extract correlation ID from context."""
    return info.context.get("correlation_id")


def _validate_page_size(first: int) -> int:
    """Validate and clamp page size to allowed range."""
    return max(_MIN_PAGE_SIZE, min(first, _MAX_PAGE_SIZE))


@strawberry.type
class Query:
    """GraphQL Query root for Examples."""

    @strawberry.field
    async def item(self, info: Info, id: str) -> ItemExampleType | None:
        """Get a single item by ID."""
        query_bus = _get_query_bus(info)
        query = GetItemQuery(item_id=id)

        logger.debug("graphql_query", operation="item", item_id=id)
        result = await query_bus.dispatch(query)

        match result:
            case Ok(item_dto):
                return map_item_dto_to_type(item_dto)
            case Err(error):
                logger.warning(
                    "graphql_query_failed",
                    operation="item",
                    error_type=type(error).__name__,
                )
                return None

    @strawberry.field
    async def items(
        self,
        info: Info,
        first: int = _DEFAULT_PAGE_SIZE,
        after: str | None = None,
        category: str | None = None,
    ) -> ItemConnection:
        """Get paginated list of items with Relay-style connection."""
        query_bus = _get_query_bus(info)
        validated_first = _validate_page_size(first)
        page = parse_cursor_to_page(after, validated_first)
        query = ListItemsQuery(page=page, size=validated_first, category=category)

        logger.debug("graphql_query", operation="items", page=page, size=validated_first)
        result = await query_bus.dispatch(query)

        match result:
            case Ok(paginated_response):
                return create_item_connection(
                    items=paginated_response.items,
                    page=page,
                    page_size=validated_first,
                    total=paginated_response.total,
                )
            case Err(error):
                logger.warning(
                    "graphql_query_failed",
                    operation="items",
                    error_type=type(error).__name__,
                )
                return create_empty_item_connection()

    @strawberry.field
    async def pedido(self, info: Info, id: str) -> PedidoExampleType | None:
        """Get a single pedido by ID."""
        query_bus = _get_query_bus(info)
        query = GetPedidoQuery(pedido_id=id)

        logger.debug("graphql_query", operation="pedido", pedido_id=id)
        result = await query_bus.dispatch(query)

        match result:
            case Ok(pedido_dto):
                return map_pedido_dto_to_type(pedido_dto)
            case Err(error):
                logger.warning(
                    "graphql_query_failed",
                    operation="pedido",
                    error_type=type(error).__name__,
                )
                return None

    @strawberry.field
    async def pedidos(
        self,
        info: Info,
        first: int = _DEFAULT_PAGE_SIZE,
        after: str | None = None,
        customer_id: str | None = None,
    ) -> PedidoConnection:
        """Get paginated list of pedidos with Relay-style connection."""
        query_bus = _get_query_bus(info)
        validated_first = _validate_page_size(first)
        page = parse_cursor_to_page(after, validated_first)
        query = ListPedidosQuery(page=page, size=validated_first, customer_id=customer_id)

        logger.debug("graphql_query", operation="pedidos", page=page, size=validated_first)
        result = await query_bus.dispatch(query)

        match result:
            case Ok(paginated_response):
                return create_pedido_connection(
                    pedidos=paginated_response.items,
                    page=page,
                    page_size=validated_first,
                    total=paginated_response.total,
                )
            case Err(error):
                logger.warning(
                    "graphql_query_failed",
                    operation="pedidos",
                    error_type=type(error).__name__,
                )
                return create_empty_pedido_connection()
