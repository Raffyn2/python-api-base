"""Service layer protocols and interfaces.

**Feature: python-api-base-2025-validation**
**Validates: Requirements 22.1, 22.2, 22.3, 22.4**

Protocols for service layer components to enable dependency injection
and loose coupling.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IEventBus(Protocol):
    """Protocol for event bus integration."""

    async def publish(self, event: dict[str, Any]) -> None:
        """Publish an event.

        Args:
            event: Event data to publish.
        """
        ...


@runtime_checkable
class IServiceMapper[TEntity, TResponse](Protocol):
    """Simplified mapper protocol for service operations.

    This is a minimal protocol requiring only to_dto for service layer.
    For full bidirectional mapping, use core.protocols.application.Mapper.

    Type Parameters:
        TEntity: Domain entity type.
        TResponse: Response DTO type.
    """

    def to_dto(self, entity: TEntity) -> TResponse:
        """Convert entity to response DTO.

        Args:
            entity: Domain entity to convert.

        Returns:
            Response DTO representation of the entity.
        """
        ...


@runtime_checkable
class IEventPublisher(Protocol):
    """Protocol for event publisher (Kafka, RabbitMQ, etc).

    Enables dependency inversion for event publishing in Application layer.
    Infrastructure implementations inject concrete publishers.
    """

    async def publish(self, event: dict[str, Any], topic: str | None = None) -> None:
        """Publish event to message broker.

        Args:
            event: Event data to publish.
            topic: Optional topic/queue name. If None, uses default routing.

        Raises:
            PublishError: If event publishing fails.
        """
        ...

    async def publish_batch(self, events: list[dict[str, Any]], topic: str | None = None) -> None:
        """Publish multiple events in batch.

        Args:
            events: List of event data to publish.
            topic: Optional topic/queue name.

        Raises:
            PublishError: If batch publishing fails.
        """
        ...
