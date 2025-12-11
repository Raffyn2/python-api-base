"""CQRS (Command Query Responsibility Segregation) infrastructure.

Re-exports CQRS components for public API.

Organized into subpackages by responsibility:
- commands/: Command base class and CommandBus
- queries/: Query base class and QueryBus
- events/: EventBus and event handling
- handlers/: CommandHandler and QueryHandler base classes
- exceptions/: CQRS-specific exceptions

**Feature: python-api-base-2025-state-of-art**
**Refactored: 2025 - Organized into subpackages by responsibility**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
"""

# Re-export from specialized subpackages
from application.common.cqrs.commands import (
    Command,
    CommandBus,
    CommandHandler,
    CommandHandlerFunc,
    MiddlewareFunc,
)
from application.common.cqrs.events import (
    EventHandler,
    EventHandlerError,
    TypedEventBus,
)
from application.common.cqrs.exceptions import (
    CQRSError,
    HandlerAlreadyRegisteredError,
    HandlerNotFoundError,
    MiddlewareError,
)
from application.common.cqrs.queries import (
    Query,
    QueryBus,
    QueryHandler,
    QueryHandlerFunc,
)
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
