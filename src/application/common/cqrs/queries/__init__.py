"""CQRS Query infrastructure.

Provides query base class and query bus for read operations.

**Feature: python-api-base-2025-state-of-art**
**Refactored: 2025 - Renamed QueryHandler to QueryHandlerFunc for clarity**
"""

from application.common.cqrs.queries.query_bus import Query, QueryBus, QueryHandlerFunc

# Backward compatibility alias
QueryHandler = QueryHandlerFunc

__all__ = [
    "Query",
    "QueryBus",
    "QueryHandler",  # Alias for backward compatibility
    "QueryHandlerFunc",
]
