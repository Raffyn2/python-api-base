"""CQRS infrastructure components.

Provides Command Query Responsibility Segregation pattern implementation:
- CommandBus: Dispatches commands to handlers
- QueryBus: Dispatches queries to handlers with caching
- EventBus: Publishes domain events to subscribers

**Architecture: CQRS Pattern**
**Refactored: 2025 - Improved exports, added new type aliases**
"""

# Re-export from bus module (main façade)
from application.common.cqrs.bus import (
    ApplicationError,
    Command,
    CommandBus,
    CommandHandler,
    CommandHandlerFunc,
    ConflictError,
    CQRSError,
    EventHandler,
    EventHandlerError,
    ForbiddenError,
    HandlerAlreadyRegisteredError,
    HandlerNotFoundError,
    MiddlewareError,
    MiddlewareFunc,
    NotFoundError,
    Query,
    QueryBus,
    QueryHandler,
    QueryHandlerFunc,
    TypedEventBus,
    UnauthorizedError,
    ValidationError,
)

__all__ = [
    # Exceptions
    "ApplicationError",
    "CQRSError",
    # Command Bus
    "Command",
    "CommandBus",
    "CommandHandler",
    "CommandHandlerFunc",
    "ConflictError",
    # Event Bus
    "EventHandler",
    "EventHandlerError",
    "ForbiddenError",
    "HandlerAlreadyRegisteredError",
    "HandlerNotFoundError",
    "MiddlewareError",
    "MiddlewareFunc",
    "NotFoundError",
    # Query Bus
    "Query",
    "QueryBus",
    "QueryHandler",
    "QueryHandlerFunc",
    "TypedEventBus",
    "UnauthorizedError",
    "ValidationError",
]
