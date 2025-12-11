"""Tests for event publishing mixin.

**Feature: realistic-test-coverage**
**Validates: Requirements 6.1**
"""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from application.common.mixins.event_publishing.event_publishing import (
    EventPublishingMixin,
)


class MockEvent:
    """Mock domain event."""

    def __init__(self, name: str = "TestEvent") -> None:
        self.name = name


class MockEntity:
    """Mock entity with events."""

    def __init__(self) -> None:
        self._events: list[Any] = []

    @property
    def events(self) -> list[Any]:
        return self._events

    def add_event(self, event: Any) -> None:
        self._events.append(event)

    def clear_events(self) -> None:
        self._events.clear()


class MockEventBus:
    """Mock event bus."""

    def __init__(self) -> None:
        self.publish = AsyncMock()
        self.published_events: list[Any] = []

    async def _publish(self, event: Any, **kwargs: Any) -> None:
        self.published_events.append(event)


class SampleUseCase(EventPublishingMixin):
    """Sample use case with event publishing mixin."""

    def __init__(self, event_bus: Any | None = None) -> None:
        self._event_bus = event_bus


class TestEventPublishingMixin:
    """Tests for EventPublishingMixin."""

    @pytest.mark.asyncio
    async def test_publish_entity_events_without_event_bus(self) -> None:
        """Test publishing events when event bus is None."""
        use_case = SampleUseCase(event_bus=None)
        entity = MockEntity()
        entity.add_event(MockEvent())

        # Should not raise
        await use_case._publish_entity_events(entity)

        # Events should still be there (not cleared without bus)
        assert len(entity.events) == 1

    @pytest.mark.asyncio
    async def test_publish_entity_events_publishes_all_events(self) -> None:
        """Test that all events are published."""
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()
        entity.add_event(MockEvent("Event1"))
        entity.add_event(MockEvent("Event2"))
        entity.add_event(MockEvent("Event3"))

        await use_case._publish_entity_events(entity)

        assert event_bus.publish.call_count == 3

    @pytest.mark.asyncio
    async def test_publish_entity_events_clears_events(self) -> None:
        """Test that events are cleared after publishing."""
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()
        entity.add_event(MockEvent())
        entity.add_event(MockEvent())

        await use_case._publish_entity_events(entity)

        assert len(entity.events) == 0

    @pytest.mark.asyncio
    async def test_publish_entity_events_handles_error(self) -> None:
        """Test that errors are handled gracefully."""
        event_bus = MockEventBus()
        event_bus.publish = AsyncMock(side_effect=Exception("Publish failed"))
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()
        entity.add_event(MockEvent())

        # Should not raise by default
        await use_case._publish_entity_events(entity, raise_on_error=False)

    @pytest.mark.asyncio
    async def test_publish_entity_events_raises_on_error_when_configured(self) -> None:
        """Test that errors are raised when raise_on_error=True."""
        event_bus = MockEventBus()
        event_bus.publish = AsyncMock(side_effect=Exception("Publish failed"))
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()
        entity.add_event(MockEvent())

        with pytest.raises(Exception, match="Publish failed"):
            await use_case._publish_entity_events(entity, raise_on_error=True)

    @pytest.mark.asyncio
    async def test_publish_events_shortcut(self) -> None:
        """Test _publish_events shortcut method."""
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()
        entity.add_event(MockEvent())

        await use_case._publish_events(entity)

        assert event_bus.publish.call_count == 1
        assert len(entity.events) == 0

    @pytest.mark.asyncio
    async def test_publish_events_does_not_raise(self) -> None:
        """Test _publish_events does not raise on error."""
        event_bus = MockEventBus()
        event_bus.publish = AsyncMock(side_effect=Exception("Error"))
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()
        entity.add_event(MockEvent())

        # Should not raise
        await use_case._publish_events(entity)

    @pytest.mark.asyncio
    async def test_publish_with_empty_events(self) -> None:
        """Test publishing when entity has no events."""
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()

        await use_case._publish_entity_events(entity)

        assert event_bus.publish.call_count == 0

    @pytest.mark.asyncio
    async def test_publish_passes_raise_on_error_to_bus(self) -> None:
        """Test that raise_on_error is passed to event bus."""
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity()
        entity.add_event(MockEvent())

        await use_case._publish_entity_events(entity, raise_on_error=True)

        event_bus.publish.assert_called_once()
        call_kwargs = event_bus.publish.call_args[1]
        assert call_kwargs["raise_on_error"] is True
