"""Unit tests for domain events and EventBus.

Tests EntityCreatedEvent, EntityUpdatedEvent, EntityDeletedEvent, and EventBus.
"""

from dataclasses import dataclass

import pytest

from core.base.events.domain_event import (
    DomainEvent,
    EntityCreatedEvent,
    EntityDeletedEvent,
    EntityUpdatedEvent,
    EventBus,
)


class TestEntityCreatedEvent:
    """Tests for EntityCreatedEvent."""

    def test_event_type(self) -> None:
        """Test event_type property."""
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        assert event.event_type == "User.created"

    def test_default_values(self) -> None:
        """Test default values."""
        event = EntityCreatedEvent()
        assert event.entity_type == ""
        assert event.entity_id == ""

    def test_event_id_generated(self) -> None:
        """Test event_id is auto-generated."""
        event = EntityCreatedEvent()
        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_occurred_at_set(self) -> None:
        """Test occurred_at is set."""
        event = EntityCreatedEvent()
        assert event.occurred_at is not None


class TestEntityUpdatedEvent:
    """Tests for EntityUpdatedEvent."""

    def test_event_type(self) -> None:
        """Test event_type property."""
        event = EntityUpdatedEvent(entity_type="User", entity_id="123")
        assert event.event_type == "User.updated"

    def test_changed_fields(self) -> None:
        """Test changed_fields."""
        event = EntityUpdatedEvent(
            entity_type="User",
            entity_id="123",
            changed_fields=("name", "email"),
        )
        assert event.changed_fields == ("name", "email")


class TestEntityDeletedEvent:
    """Tests for EntityDeletedEvent."""

    def test_event_type(self) -> None:
        """Test event_type property."""
        event = EntityDeletedEvent(entity_type="User", entity_id="123")
        assert event.event_type == "User.deleted"

    def test_soft_delete_default(self) -> None:
        """Test soft_delete defaults to True."""
        event = EntityDeletedEvent()
        assert event.soft_delete is True

    def test_hard_delete(self) -> None:
        """Test hard delete."""
        event = EntityDeletedEvent(soft_delete=False)
        assert event.soft_delete is False


class TestEventBus:
    """Tests for EventBus."""

    def test_subscribe_to_event_type(self) -> None:
        """Test subscribing to specific event type."""
        bus = EventBus()
        handled = []

        def handler(event: DomainEvent) -> None:
            handled.append(event)

        bus.subscribe("User.created", handler)
        
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        bus.publish_sync(event)
        
        assert len(handled) == 1
        assert handled[0] == event

    def test_subscribe_global(self) -> None:
        """Test subscribing to all events."""
        bus = EventBus()
        handled = []

        def handler(event: DomainEvent) -> None:
            handled.append(event)

        bus.subscribe(None, handler)
        
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        bus.publish_sync(event)
        
        assert len(handled) == 1

    def test_subscribe_as_decorator(self) -> None:
        """Test subscribe as decorator."""
        bus = EventBus()
        handled = []

        @bus.subscribe("User.created")
        def handler(event: DomainEvent) -> None:
            handled.append(event)

        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        bus.publish_sync(event)
        
        assert len(handled) == 1

    def test_unsubscribe(self) -> None:
        """Test unsubscribing handler."""
        bus = EventBus()
        handled = []

        def handler(event: DomainEvent) -> None:
            handled.append(event)

        bus.subscribe("User.created", handler)
        bus.unsubscribe("User.created", handler)
        
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        bus.publish_sync(event)
        
        assert len(handled) == 0

    def test_unsubscribe_global(self) -> None:
        """Test unsubscribing global handler."""
        bus = EventBus()
        handled = []

        def handler(event: DomainEvent) -> None:
            handled.append(event)

        bus.subscribe(None, handler)
        bus.unsubscribe(None, handler)
        
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        bus.publish_sync(event)
        
        assert len(handled) == 0

    def test_handler_exception_logged(self) -> None:
        """Test handler exception is logged but doesn't stop other handlers."""
        bus = EventBus()
        handled = []

        def failing_handler(event: DomainEvent) -> None:
            raise ValueError("Test error")

        def success_handler(event: DomainEvent) -> None:
            handled.append(event)

        bus.subscribe("User.created", failing_handler)
        bus.subscribe("User.created", success_handler)
        
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        bus.publish_sync(event)
        
        # Second handler should still be called
        assert len(handled) == 1

    @pytest.mark.asyncio
    async def test_publish_async(self) -> None:
        """Test async publish."""
        bus = EventBus()
        handled = []

        def handler(event: DomainEvent) -> None:
            handled.append(event)

        bus.subscribe("User.created", handler)
        
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        await bus.publish(event)
        
        assert len(handled) == 1

    @pytest.mark.asyncio
    async def test_publish_async_handler(self) -> None:
        """Test async handler."""
        bus = EventBus()
        handled = []

        async def async_handler(event: DomainEvent) -> None:
            handled.append(event)

        bus.subscribe("User.created", async_handler)
        
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        await bus.publish(event)
        
        assert len(handled) == 1

    def test_no_handlers(self) -> None:
        """Test publish with no handlers."""
        bus = EventBus()
        event = EntityCreatedEvent(entity_type="User", entity_id="123")
        
        # Should not raise
        bus.publish_sync(event)
