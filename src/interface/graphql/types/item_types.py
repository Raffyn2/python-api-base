"""GraphQL types for ItemExample.

**Feature: interface-modules-workflow-analysis**
**Validates: Requirements 3.1, 3.2, 3.3**
"""

from datetime import datetime

import strawberry

from interface.graphql.types.shared_types import PageInfoType


@strawberry.type
class ItemExampleType:
    """GraphQL type for ItemExample."""

    id: str
    name: str
    description: str | None
    category: str
    price: float
    quantity: int
    status: str
    created_at: datetime
    updated_at: datetime | None


@strawberry.type
class ItemEdge:
    """Edge type for Item connection."""

    node: ItemExampleType
    cursor: str


@strawberry.type
class ItemConnection:
    """Relay-style connection for Items."""

    edges: list[ItemEdge]
    page_info: PageInfoType
    total_count: int


@strawberry.input
class ItemCreateInput:
    """Input for creating an Item."""

    name: str
    sku: str
    category: str
    price: float
    description: str | None = None
    quantity: int = 0


@strawberry.input
class ItemUpdateInput:
    """Input for updating an Item."""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    quantity: int | None = None


@strawberry.type
class ItemMutationResult:
    """Result of Item mutation."""

    success: bool
    item: ItemExampleType | None = None
    error: str | None = None
