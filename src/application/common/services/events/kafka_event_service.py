"""Kafka event publishing service.

Provides centralized Kafka event publishing with consistent error handling.

**Feature: application-layer-code-review-2025**
**Extracted from: examples/item/use_case.py**
"""

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from infrastructure.kafka.event_publisher import EventPublisher

logger = structlog.get_logger(__name__)


class KafkaEventService:
    """Service for publishing domain events to Kafka.

    Centralizes Kafka event publishing with consistent error handling
    and logging.

    Example:
        >>> kafka_service = KafkaEventService(kafka_publisher)
        >>> await kafka_service.publish_event(
        ...     event_type="ItemCreated",
        ...     entity_type="Item",
        ...     entity_id="123",
        ...     payload=ItemCreatedEvent(...),
        ... )
    """

    def __init__(self, publisher: "EventPublisher | None" = None) -> None:
        """Initialize Kafka event service.

        Args:
            publisher: Optional Kafka event publisher.
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
            from infrastructure.kafka.event_publisher import DomainEvent

            kafka_event = DomainEvent(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
            )
            await self._publisher.publish(kafka_event, topic)

            logger.debug(
                "Kafka event published",
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                topic=topic,
            )
            return True

        except Exception:
            logger.exception(
                "Failed to publish Kafka event",
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            return False
