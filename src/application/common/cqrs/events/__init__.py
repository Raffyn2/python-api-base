"""Domain Event Bus infrastructure.

Provides event handler protocol and typed event bus for domain events.

**Feature: python-api-base-2025-state-of-art**
**Refactored: 2025 - EventHandlerError moved to exceptions module**
"""

from application.common.cqrs.events.event_bus import (
    EventHandler,
    TypedEventBus,
)
from application.common.cqrs.exceptions.exceptions import EventHandlerError

__all__ = [
    "EventHandler",
    "EventHandlerError",
    "TypedEventBus",
]
