"""Tests for EventPublishingMixin.

Tests event publishing functionality for use cases.
"""

from typing import Any

import pytest

from application.common.mixins.event_publishing import EventPublishingMixin


class MockEvent:
    """Mock event for testing."""

    def __init__(self, name: str = "TestEvent") -> None:
        self.name = name


class MockEntity:
    """Mock entity with events for testing."""

    def __init__(self, events: list[Any] | None = None) -> None:
        self._events = events or []

    @property
    def events(self) -> list[Any]:
        return self._events

    def clear_events(self) -> None:
        self._events.clear()


class MockEventBus:
    """Mock event bus for testing."""

    def __init__(self, should_fail: bool = False) -> None:
        self.published_events: list[Any] = []
        self.should_fail = should_fail

    async def publish(self, event: Any, **kwargs: Any) -> None:
        if self.should_fail:
            raise RuntimeError("Event bus failure")
        self.published_events.append(event)


class SampleUseCase(EventPublishingMixin):
    """Sample use case that uses the mixin."""

    def __init__(self, event_bus: MockEventBus | None = None) -> None:
        self._event_bus = event_bus


class TestEventPublishingMixinBasic:
    """Tests for basic event publishing."""

    @pytest.mark.asyncio
    async def test_publish_single_event(self) -> None:
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[MockEvent("Event1")])

        await use_case._publish_entity_events(entity)

        assert len(event_bus.published_events) == 1
        assert event_bus.published_events[0].name == "Event1"

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self) -> None:
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[MockEvent("Event1"), MockEvent("Event2")])

        await use_case._publish_entity_events(entity)

        assert len(event_bus.published_events) == 2

    @pytest.mark.asyncio
    async def test_clears_events_after_publishing(self) -> None:
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[MockEvent("Event1")])

        await use_case._publish_entity_events(entity)

        assert len(entity.events) == 0

    @pytest.mark.asyncio
    async def test_no_event_bus_does_nothing(self) -> None:
        use_case = SampleUseCase(event_bus=None)
        entity = MockEntity(events=[MockEvent("Event1")])

        await use_case._publish_entity_events(entity)

        # Events should not be cleared when no event bus
        assert len(entity.events) == 1


class TestEventPublishingMixinErrorHandling:
    """Tests for error handling in event publishing."""

    @pytest.mark.asyncio
    async def test_error_logged_but_not_raised_by_default(self) -> None:
        event_bus = MockEventBus(should_fail=True)
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[MockEvent("Event1")])

        # Should not raise
        await use_case._publish_entity_events(entity)

    @pytest.mark.asyncio
    async def test_error_raised_when_raise_on_error_true(self) -> None:
        event_bus = MockEventBus(should_fail=True)
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[MockEvent("Event1")])

        with pytest.raises(RuntimeError, match="Event bus failure"):
            await use_case._publish_entity_events(entity, raise_on_error=True)


class TestEventPublishingMixinShortcut:
    """Tests for _publish_events shortcut method."""

    @pytest.mark.asyncio
    async def test_publish_events_shortcut(self) -> None:
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[MockEvent("Event1")])

        await use_case._publish_events(entity)

        assert len(event_bus.published_events) == 1
        assert len(entity.events) == 0

    @pytest.mark.asyncio
    async def test_publish_events_shortcut_does_not_raise(self) -> None:
        event_bus = MockEventBus(should_fail=True)
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[MockEvent("Event1")])

        # Should not raise
        await use_case._publish_events(entity)


class TestEventPublishingMixinEmptyEvents:
    """Tests for empty event scenarios."""

    @pytest.mark.asyncio
    async def test_empty_events_list(self) -> None:
        event_bus = MockEventBus()
        use_case = SampleUseCase(event_bus=event_bus)
        entity = MockEntity(events=[])

        await use_case._publish_entity_events(entity)

        assert len(event_bus.published_events) == 0
