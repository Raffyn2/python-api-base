"""CQRS Query Bus infrastructure.

This module provides:
- Query base class for read operations
- QueryBus for dispatching queries to handlers
- Caching support for query results

**Feature: python-api-base-2025-state-of-art**
**Validates: Requirements 2.2**
**Refactored: 2025 - Fixed logging, improved type safety**
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from application.common.cqrs.exceptions.exceptions import HandlerNotFoundError

logger = structlog.get_logger(__name__)

# Module constants
_LOG_OP_REGISTER = "QUERY_REGISTER"
_LOG_OP_DISPATCH = "QUERY_DISPATCH"
_LOG_OP_CACHE = "QUERY_CACHE"


# =============================================================================
# Query Base Class
# =============================================================================


class Query[T](ABC):
    """Base class for CQRS queries.

    Queries represent requests for data without side effects.
    They should be immutable and contain all parameters needed.

    **Feature: advanced-reusability**
    **Validates: Requirements 5.2**

    Type Parameters:
        T: The type of data returned by the query.

    Example:
        >>> class GetUserQuery(Query[User]):
        ...     def __init__(self, user_id: str):
        ...         self.user_id = user_id
        ...
        ...     async def execute(self) -> User:
        ...         # Query execution logic
        ...         pass
    """

    @abstractmethod
    async def execute(self) -> T:
        """Execute the query.

        Returns:
            The query result data.
        """
        ...


# =============================================================================
# Query Handler Types
# =============================================================================

type QueryHandlerFunc = Callable[[Any], Awaitable[Any]]
"""Type alias for query handler functions.

A query handler is an async function that takes a query and returns the result data.
Note: Named QueryHandlerFunc to avoid conflict with QueryHandler class in handlers.py.
"""


# =============================================================================
# Query Bus
# =============================================================================


class QueryBus:
    """Dispatches queries to registered handlers.

    Supports caching of query results for performance optimization.

    **Feature: advanced-reusability**
    **Validates: Requirements 5.4**

    Example:
        >>> bus = QueryBus()
        >>> bus.register(GetUserQuery, get_user_handler)
        >>> user = await bus.dispatch(GetUserQuery(user_id="123"))
    """

    def __init__(self) -> None:
        """Initialize query bus."""
        self._handlers: dict[type, QueryHandlerFunc] = {}
        self._cache: Any = None

    def register(
        self,
        query_type: type[Query[Any]],
        handler: QueryHandlerFunc,
    ) -> None:
        """Register a handler for a query type.

        Args:
            query_type: The query class to handle.
            handler: Async function that handles the query.

        Raises:
            ValueError: If handler is already registered for this type.
        """
        if query_type in self._handlers:
            msg = f"Handler already registered for {query_type.__name__}"
            raise ValueError(msg)
        self._handlers[query_type] = handler
        logger.debug(
            "Registered query handler",
            query_type=query_type.__name__,
            operation=_LOG_OP_REGISTER,
        )

    def unregister(self, query_type: type[Query[Any]]) -> None:
        """Unregister a handler for a query type.

        Args:
            query_type: The query class to unregister.
        """
        self._handlers.pop(query_type, None)
        logger.debug(
            "Unregistered query handler",
            query_type=query_type.__name__,
        )

    def set_cache(self, cache: Any) -> None:
        """Set cache provider for query results.

        Args:
            cache: Cache provider implementing get/set methods.
        """
        self._cache = cache
        logger.debug(
            "Cache provider configured",
            operation=_LOG_OP_CACHE,
        )

    async def dispatch[T](self, query: Query[T]) -> T:
        """Dispatch a query to its registered handler.

        Args:
            query: The query to dispatch.

        Returns:
            Query result from the handler.

        Raises:
            HandlerNotFoundError: If no handler is registered.
        """
        query_type = type(query)
        handler = self._handlers.get(query_type)

        if handler is None:
            raise HandlerNotFoundError(query_type)

        # Check cache if available
        cache_key = self._get_cache_key(query)
        if self._cache is not None and cache_key:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                logger.debug(
                    "Cache hit",
                    query_type=query_type.__name__,
                    cache_key=cache_key,
                    operation=_LOG_OP_CACHE,
                )
                return cached

        # Execute query
        logger.debug(
            "Dispatching query",
            query_type=query_type.__name__,
            operation=_LOG_OP_DISPATCH,
        )
        result = await handler(query)

        # Cache result if caching is enabled
        if self._cache is not None and cache_key:
            ttl = getattr(query, "cache_ttl", None)
            await self._cache.set(cache_key, result, ttl)
            logger.debug(
                "Cached query result",
                query_type=query_type.__name__,
                cache_key=cache_key,
                ttl=ttl,
                operation=_LOG_OP_CACHE,
            )

        return result

    def _get_cache_key(self, query: Query[Any]) -> str | None:
        """Generate cache key for a query.

        Args:
            query: The query to generate key for.

        Returns:
            Cache key string or None if not cacheable.
        """
        if hasattr(query, "cache_key"):
            return query.cache_key

        if not getattr(query, "cacheable", False):
            return None

        query_type = type(query).__name__
        attrs = {k: v for k, v in query.__dict__.items() if not k.startswith("_")}
        return f"{query_type}:{hash(frozenset(attrs.items()))}"
