"""CQRS infrastructure components.

Provides Command Query Responsibility Segregation pattern implementation:
- CommandBus: Dispatches commands to handlers
- QueryBus: Dispatches queries to handlers with caching
- EventBus: Publishes domain events to subscribers

**Architecture: CQRS Pattern**
"""

# Re-export exceptions from bus module
from application.common.cqrs.bus import (
    ApplicationError,
    ConflictError,
    ForbiddenError,
    HandlerNotFoundError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from application.common.cqrs.command_bus import (
    Command,
    CommandBus,
    CommandHandler,
    MiddlewareFunc,
)
from application.common.cqrs.event_bus import (
    EventHandler,
    EventHandlerError,
    TypedEventBus,
)
from application.common.cqrs.query_bus import Query, QueryBus, QueryHandler

__all__ = [
    # Exceptions
    "ApplicationError",
    # Command Bus
    "Command",
    "CommandBus",
    "CommandHandler",
    "ConflictError",
    # Event Bus
    "EventHandler",
    "EventHandlerError",
    "ForbiddenError",
    "HandlerNotFoundError",
    "MiddlewareFunc",
    "NotFoundError",
    # Query Bus
    "Query",
    "QueryBus",
    "QueryHandler",
    "TypedEventBus",
    "UnauthorizedError",
    "ValidationError",
]
