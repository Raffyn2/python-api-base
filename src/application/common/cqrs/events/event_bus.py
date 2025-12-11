"""Domain Event Bus infrastructure.

This module provides:
- EventHandler protocol (re-exported from core.protocols)
- TypedEventBus for publishing domain events
- Subscription management for event handlers
- Proper error propagation with EventHandlerError

**Feature: python-api-base-2025-state-of-art**
**Validates: Requirements 2.4**
**Refactored: 2025 - Consolidated EventHandler to core.protocols**
"""

from typing import Any

import structlog

from application.common.cqrs.exceptions.exceptions import EventHandlerError

# Import canonical EventHandler from core.protocols (Single Source of Truth)
from core.protocols.application import EventHandler

logger = structlog.get_logger(__name__)

# Module constants
_LOG_OP_SUBSCRIBE = "EVENT_SUBSCRIBE"
_LOG_OP_PUBLISH = "EVENT_PUBLISH"
_LOG_OP_ERROR = "EVENT_HANDLER_ERROR"

# Re-export for backward compatibility
__all__ = ["EventHandler", "TypedEventBus"]


# =============================================================================
# Typed Event Bus
# =============================================================================


class TypedEventBus[TEvent]:
    """Typed event bus for publishing domain events.

    Type Parameters:
        TEvent: Base event type for this bus.

    **Feature: python-api-base-2025-state-of-art**
    **Validates: Requirements 2.4**

    Example:
        >>> bus = TypedEventBus()
        >>> bus.subscribe(UserCreatedEvent, user_created_handler)
        >>> await bus.publish(UserCreatedEvent(user_id="123"))
    """

    def __init__(self) -> None:
        """Initialize typed event bus."""
        self._handlers: dict[type, list[EventHandler[Any]]] = {}

    def subscribe[T: TEvent](
        self,
        event_type: type[T],
        handler: EventHandler[T],
    ) -> None:
        """Subscribe handler to event type.

        Args:
            event_type: The event type to subscribe to.
            handler: Handler to call when event is published.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(
            "Subscribed handler to event type",
            event_type=event_type.__name__,
            handler=type(handler).__name__,
            operation=_LOG_OP_SUBSCRIBE,
        )

    def unsubscribe[T: TEvent](
        self,
        event_type: type[T],
        handler: EventHandler[T],
    ) -> None:
        """Unsubscribe handler from event type.

        Args:
            event_type: The event type to unsubscribe from.
            handler: Handler to remove.
        """
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]
            logger.debug(
                "Unsubscribed handler from event type",
                event_type=event_type.__name__,
                handler=type(handler).__name__,
            )

    async def publish(
        self,
        event: TEvent,
        *,
        raise_on_error: bool = True,
    ) -> list[Exception]:
        """Publish event to all subscribed handlers.

        Args:
            event: The event to publish.
            raise_on_error: If True, raises EventHandlerError on failures.
                           If False, returns list of exceptions.

        Returns:
            List of exceptions from failed handlers (empty if all succeeded).

        Raises:
            EventHandlerError: If any handler fails and raise_on_error is True.
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        errors: list[tuple[str, Exception]] = []

        for handler in handlers:
            handler_name = type(handler).__name__
            try:
                await handler.handle(event)
                logger.debug(
                    "Event handled successfully",
                    event_type=event_type.__name__,
                    handler=handler_name,
                    operation=_LOG_OP_PUBLISH,
                )
            except Exception as e:
                logger.exception(
                    "Event handler failed",
                    event_type=event_type.__name__,
                    handler=handler_name,
                    operation=_LOG_OP_ERROR,
                )
                errors.append((handler_name, e))

        if errors and raise_on_error:
            raise EventHandlerError(
                event_type=event_type.__name__,
                handler_errors=errors,
            )

        return [e for _, e in errors]
