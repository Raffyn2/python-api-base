"""GraphQL support module.

**Feature: python-api-base-2025-generics-audit**
**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 20.1-20.5, 3.1, 3.2, 3.3**
"""

from interface.graphql.dataloader import DataLoader, DataLoaderConfig
from interface.graphql.mapper import GraphQLType, PydanticGraphQLMapper
from interface.graphql.relay import Connection, Edge, PageInfo
from interface.graphql.resolvers import (
    BaseMutationResolver,
    BaseQueryResolver,
    BaseSubscription,
    MutationResolver,
    QueryArgs,
    QueryResolver,
    Subscription,
)

# Import router and schema for integration
try:
    from interface.graphql.router import router as graphql_router
    from interface.graphql.schema import schema as graphql_schema

    HAS_STRAWBERRY = True
except ImportError:
    graphql_router = None
    graphql_schema = None
    HAS_STRAWBERRY = False

__all__ = [
    "HAS_STRAWBERRY",
    # Resolvers
    "BaseMutationResolver",
    "BaseQueryResolver",
    "BaseSubscription",
    # Relay
    "Connection",
    # DataLoader
    "DataLoader",
    "DataLoaderConfig",
    "Edge",
    # Mapper
    "GraphQLType",
    "MutationResolver",
    "PageInfo",
    "PydanticGraphQLMapper",
    "QueryArgs",
    "QueryResolver",
    "Subscription",
    # Router
    "graphql_router",
    "graphql_schema",
]
