"""Unit tests for core/base/domain/aggregate_root.py.

Tests aggregate root domain event handling and version management.

**Feature: test-coverage-90-percent**
**Validates: Requirements 3.1**
"""

from core.base.domain.aggregate_root import AggregateRoot
from core.base.events.domain_event import DomainEvent


class TestDomainEvent(DomainEvent):
    """Test domain event for testing."""

    data: str = "test"

    @property
    def event_type(self) -> str:
        """Return event type."""
        return "test_event"


class TestAggregateRoot:
    """Tests for AggregateRoot class."""

    def test_create_aggregate_with_defaults(self) -> None:
        """AggregateRoot should be created with default values."""
        aggregate = AggregateRoot[str]()

        assert aggregate.id is None
        assert aggregate.version == 1
        assert aggregate.is_deleted is False

    def test_create_aggregate_with_id(self) -> None:
        """AggregateRoot should accept custom ID."""
        aggregate = AggregateRoot[str](id="agg-123")

        assert aggregate.id == "agg-123"

    def test_add_event(self) -> None:
        """add_event should add event to pending events."""
        aggregate = AggregateRoot[str]()
        event = TestDomainEvent()

        aggregate.add_event(event)

        assert len(aggregate.get_pending_events()) == 1
        assert aggregate.get_pending_events()[0] == event

    def test_add_multiple_events(self) -> None:
        """add_event should accumulate events."""
        aggregate = AggregateRoot[str]()
        event1 = TestDomainEvent()
        event2 = TestDomainEvent()

        aggregate.add_event(event1)
        aggregate.add_event(event2)

        events = aggregate.get_pending_events()
        assert len(events) == 2

    def test_get_pending_events_returns_copy(self) -> None:
        """get_pending_events should return a copy, not the original list."""
        aggregate = AggregateRoot[str]()
        event = TestDomainEvent()
        aggregate.add_event(event)

        events = aggregate.get_pending_events()
        events.clear()  # Modify the returned list

        # Original should be unchanged
        assert len(aggregate.get_pending_events()) == 1

    def test_clear_events_returns_and_clears(self) -> None:
        """clear_events should return events and clear the list."""
        aggregate = AggregateRoot[str]()
        event1 = TestDomainEvent()
        event2 = TestDomainEvent()
        aggregate.add_event(event1)
        aggregate.add_event(event2)

        cleared = aggregate.clear_events()

        assert len(cleared) == 2
        assert len(aggregate.get_pending_events()) == 0

    def test_has_pending_events_true(self) -> None:
        """has_pending_events should return True when events exist."""
        aggregate = AggregateRoot[str]()
        aggregate.add_event(TestDomainEvent())

        assert aggregate.has_pending_events() is True

    def test_has_pending_events_false(self) -> None:
        """has_pending_events should return False when no events."""
        aggregate = AggregateRoot[str]()

        assert aggregate.has_pending_events() is False

    def test_has_pending_events_false_after_clear(self) -> None:
        """has_pending_events should return False after clearing."""
        aggregate = AggregateRoot[str]()
        aggregate.add_event(TestDomainEvent())
        aggregate.clear_events()

        assert aggregate.has_pending_events() is False

    def test_increment_version(self) -> None:
        """increment_version should increase version number."""
        aggregate = AggregateRoot[str]()

        aggregate.increment_version()

        assert aggregate.version == 2

    def test_increment_version_multiple_times(self) -> None:
        """increment_version should work multiple times."""
        aggregate = AggregateRoot[str]()

        aggregate.increment_version()
        aggregate.increment_version()
        aggregate.increment_version()

        assert aggregate.version == 4

    def test_increment_version_updates_timestamp(self) -> None:
        """increment_version should also update timestamp."""
        aggregate = AggregateRoot[str]()
        original_updated_at = aggregate.updated_at

        aggregate.increment_version()

        assert aggregate.updated_at >= original_updated_at

    def test_apply_event_adds_to_pending(self) -> None:
        """apply_event should add event to pending events."""
        aggregate = AggregateRoot[str]()
        event = TestDomainEvent()

        aggregate.apply_event(event)

        assert len(aggregate.get_pending_events()) == 1

    def test_model_post_init_initializes_events(self) -> None:
        """model_post_init should initialize _pending_events."""
        aggregate = AggregateRoot[str]()

        # Should not raise and should have empty events list
        assert aggregate.get_pending_events() == []

    def test_aggregate_inherits_base_entity_methods(self) -> None:
        """AggregateRoot should have BaseEntity methods."""
        aggregate = AggregateRoot[str]()

        aggregate.mark_deleted()
        assert aggregate.is_deleted is True

        aggregate.mark_restored()
        assert aggregate.is_deleted is False
