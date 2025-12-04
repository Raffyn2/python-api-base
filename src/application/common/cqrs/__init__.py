"""CQRS infrastructure components.

Provides Command Query Responsibility Segregation pattern implementation:
- CommandBus: Dispatches commands to handlers
- QueryBus: Dispatches queries to handlers with caching
- EventBus: Publishes domain events to subscribers

**Architecture: CQRS Pattern**
"""

# Re-export exceptions from bus module
from .bus import (
    ApplicationError,
    ConflictError,
    ForbiddenError,
    HandlerNotFoundError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from .command_bus import Command, CommandBus, CommandHandler, MiddlewareFunc
from .event_bus import EventHandler, EventHandlerError, TypedEventBus
from .query_bus import Query, QueryBus, QueryHandler

__all__ = [
    # Command Bus
    "Command",
    "CommandBus",
    "CommandHandler",
    "MiddlewareFunc",
    # Query Bus
    "Query",
    "QueryBus",
    "QueryHandler",
    # Event Bus
    "EventHandler",
    "EventHandlerError",
    "TypedEventBus",
    # Exceptions
    "ApplicationError",
    "ConflictError",
    "ForbiddenError",
    "HandlerNotFoundError",
    "NotFoundError",
    "UnauthorizedError",
    "ValidationError",
]
