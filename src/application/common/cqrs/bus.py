"""CQRS (Command Query Responsibility Segregation) infrastructure.

Re-exports CQRS components for public API.

**Feature: python-api-base-2025-state-of-art**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

# Re-export from existing modules
# Re-export errors from core.errors
from core.errors import (
    ApplicationError,
    AuthenticationError as UnauthorizedError,
    AuthorizationError as ForbiddenError,
    ConflictError,
    EntityNotFoundError as NotFoundError,
    ValidationError,
)

from .command_bus import Command, CommandBus, CommandHandler
from .event_bus import EventHandler, EventHandlerError, TypedEventBus
from .exceptions import HandlerNotFoundError
from .query_bus import Query, QueryBus, QueryHandler

# Re-export all for public API
__all__ = [
    # Exceptions
    "ApplicationError",
    "ConflictError",
    "ForbiddenError",
    "HandlerNotFoundError",
    "NotFoundError",
    "UnauthorizedError",
    "ValidationError",
    # Event Bus
    "EventHandler",
    "EventHandlerError",
    "TypedEventBus",
    # Command Bus
    "Command",
    "CommandBus",
    "CommandHandler",
    # Query Bus
    "Query",
    "QueryBus",
    "QueryHandler",
]
