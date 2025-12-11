"""Kafka event publishing service.

Provides centralized Kafka event publishing with consistent error handling.

**Feature: application-layer-code-review-2025**
**Feature: architecture-clean-layer-separation**
**Extracted from: examples/item/use_case.py**

Uses IEventPublisher Protocol for dependency inversion (Clean Architecture).
"""

from typing import Any

import structlog

from application.common.services.protocols import IEventPublisher

logger = structlog.get_logger(__name__)


class KafkaEventService:
    """Service for publishing domain events to Kafka.

    Centralizes Kafka event publishing with consistent error handling
    and logging. Uses IEventPublisher Protocol for Clean Architecture compliance.

    Example:
        >>> kafka_service = KafkaEventService(kafka_publisher)
        >>> await kafka_service.publish_event(
        ...     event_type="ItemCreated",
        ...     entity_type="Item",
        ...     entity_id="123",
        ...     payload=ItemCreatedEvent(...),
        ... )
    """

    def __init__(self, publisher: IEventPublisher | None = None) -> None:
        """Initialize Kafka event service.

        Args:
            publisher: Optional event publisher (Kafka, RabbitMQ, etc).
                      Injected via DI for testability.
        """
        self._publisher = publisher

    @property
    def is_enabled(self) -> bool:
        """Check if Kafka publishing is enabled."""
        return self._publisher is not None

    async def publish_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        payload: Any,
        topic: str = "domain-events",
    ) -> bool:
        """Publish domain event to Kafka.

        Args:
            event_type: Type of event (e.g., ItemCreated, ItemUpdated).
            entity_type: Type of entity (e.g., Item, User).
            entity_id: ID of the affected entity.
            payload: Event-specific payload dataclass.
            topic: Kafka topic (default: domain-events).

        Returns:
            True if published successfully, False otherwise.
        """
        if not self._publisher:
            return False

        try:
            # Build event dict - Protocol accepts dict[str, Any]
            kafka_event = {
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "payload": payload,
            }
            await self._publisher.publish(kafka_event, topic)

            logger.debug(
                "Event published",
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                topic=topic,
            )
            return True

        except Exception:
            logger.exception(
                "Failed to publish event",
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            return False
