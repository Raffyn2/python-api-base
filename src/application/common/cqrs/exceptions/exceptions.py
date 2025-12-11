"""CQRS exceptions module.

**Feature: python-api-base-2025-state-of-art**
**Validates: Requirements 2.1**
**Refactored: 2025 - Added EventHandlerError, improved consistency**
"""


class CQRSError(Exception):
    """Base exception for CQRS errors."""


class HandlerNotFoundError(CQRSError):
    """Raised when no handler is registered for a command/query type."""

    def __init__(self, command_type: type) -> None:
        self.command_type = command_type
        super().__init__(f"No handler registered for {command_type.__name__}")


class HandlerAlreadyRegisteredError(CQRSError):
    """Raised when trying to register a handler that already exists."""

    def __init__(self, command_type: type) -> None:
        self.command_type = command_type
        super().__init__(f"Handler already registered for {command_type.__name__}")


class MiddlewareError(CQRSError):
    """Raised when middleware execution fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EventHandlerError(CQRSError):
    """Raised when one or more event handlers fail.

    Aggregates multiple handler failures into a single exception.
    """

    def __init__(
        self,
        event_type: str,
        handler_errors: list[tuple[str, Exception]],
    ) -> None:
        """Initialize event handler error.

        Args:
            event_type: Name of the event type.
            handler_errors: List of (handler_name, exception) tuples.
        """
        self.event_type = event_type
        self.handler_errors = handler_errors
        error_count = len(handler_errors)
        super().__init__(f"{error_count} handler(s) failed for event {event_type}")
