"""Reusable mixins for application layer.

Mixins for common application patterns.

Organized into subpackages by responsibility:
- event_publishing/: Mixin for domain event publishing

**Feature: architecture-restructuring-2025**
"""

from application.common.mixins.event_publishing import (
    EventBusProtocol,
    EventPublishingMixin,
    HasEvents,
)

__all__ = [
    "EventBusProtocol",
    "EventPublishingMixin",
    "HasEvents",
]
