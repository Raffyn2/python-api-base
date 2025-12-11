"""GraphQL resolvers.

Contains data loaders for N+1 prevention.

Note: Base resolver classes were removed as they were not used.
The project uses Strawberry decorators directly (@strawberry.field, @strawberry.mutation).

**Feature: interface-restructuring-2025**
"""

from interface.graphql.resolvers.dataloader import DataLoader, DataLoaderConfig

__all__ = [
    "DataLoader",
    "DataLoaderConfig",
]
