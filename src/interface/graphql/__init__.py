"""GraphQL support module.

Organized into subpackages by responsibility:
- core/: Schema and router setup
- queries/: Query definitions
- mutations/: Mutation definitions
- resolvers/: DataLoader for N+1 prevention
- mappers/: DTO mappers (centralized in application.mappers.graphql)
- relay/: Relay pagination types (re-exports from types/)
- types/: GraphQL type definitions (Strawberry)

**Feature: python-api-base-2025-generics-audit**
**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 20.1-20.5, 3.1, 3.2, 3.3**
"""

from interface.graphql.relay import PageInfoType
from interface.graphql.resolvers import DataLoader, DataLoaderConfig

# Import router and schema for integration
try:
    from interface.graphql.core import graphql_router, schema as graphql_schema

    HAS_STRAWBERRY = True
except ImportError:
    graphql_router = None
    graphql_schema = None
    HAS_STRAWBERRY = False

__all__ = [
    "HAS_STRAWBERRY",
    # Resolvers
    "DataLoader",
    "DataLoaderConfig",
    # Relay
    "PageInfoType",
    # Core
    "graphql_router",
    "graphql_schema",
]
