"""GraphQL Schema for Examples using Strawberry.

Provides GraphQL queries and mutations for ItemExample and PedidoExample.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.1, 3.2, 3.3**
**Refactored: Split into types/, queries.py, mutations.py, mappers.py**
"""

import strawberry
from strawberry.extensions import QueryDepthLimiter

from interface.graphql.mutations import Mutation
from interface.graphql.queries import Query

# Security: Limit query depth to prevent DoS attacks
_MAX_QUERY_DEPTH = 10

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=_MAX_QUERY_DEPTH),
    ],
)

# Re-export for backward compatibility
__all__ = ["Mutation", "Query", "schema"]
