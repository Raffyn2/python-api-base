"""CQRS (Command Query Responsibility Segregation) infrastructure.

Re-exports CQRS components for public API.

**Feature: python-api-base-2025-state-of-art**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

# Re-export from existing modules
# Re-export errors from core.errors
from application.common.cqrs.command_bus import Command, CommandBus, CommandHandler
from application.common.cqrs.event_bus import (
    EventHandler,
    EventHandlerError,
    TypedEventBus,
)
from application.common.cqrs.exceptions import HandlerNotFoundError
from application.common.cqrs.query_bus import Query, QueryBus, QueryHandler
from core.errors import (
    ApplicationError,
    AuthenticationError as UnauthorizedError,
    AuthorizationError as ForbiddenError,
    ConflictError,
    EntityNotFoundError as NotFoundError,
    ValidationError,
)

# Re-export all for public API
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
    "NotFoundError",
    # Query Bus
    "Query",
    "QueryBus",
    "QueryHandler",
    "TypedEventBus",
    "UnauthorizedError",
    "ValidationError",
]
