"""GraphQL Router integration with FastAPI.

Provides the GraphQL endpoint using Strawberry with CQRS buses.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.1, 3.2, 3.3**
"""

from typing import Any

from fastapi import APIRouter, Depends, Request
from strawberry.fastapi import GraphQLRouter

from application.common.cqrs import CommandBus, QueryBus
from infrastructure.observability.correlation_id import generate_id
from interface.dependencies import get_command_bus, get_query_bus
from interface.graphql.core.schema import schema

# Header name for correlation ID
_CORRELATION_HEADER = "X-Correlation-ID"


def _extract_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID from request headers."""
    correlation_id = request.headers.get(_CORRELATION_HEADER)
    if not correlation_id:
        correlation_id = generate_id()
    return correlation_id


async def get_context(
    request: Request,
    query_bus: QueryBus = Depends(get_query_bus),
    command_bus: CommandBus = Depends(get_command_bus),
) -> dict[str, Any]:
    """Build GraphQL context with CQRS buses and correlation ID.

    **Feature: interface-modules-workflow-analysis**
    **Validates: Requirements 3.1**
    """
    correlation_id = _extract_correlation_id(request)

    return {
        "request": request,
        "query_bus": query_bus,
        "command_bus": command_bus,
        "correlation_id": correlation_id,
    }


graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    path="/graphql",
)

router = APIRouter(tags=["GraphQL"])
router.include_router(graphql_router, prefix="")
