"""Unit tests for AggregateRoot base class.

Tests event collection, version management, and aggregate lifecycle.
"""

from dataclasses import dataclass

from pydantic import Field

from core.base.domain.aggregate_root import AggregateRoot
from core.base.events.domain_event import DomainEvent


@dataclass(frozen=True, slots=True)
class SampleEvent(DomainEvent):
    """Sample event for testing."""

    message: str = ""

    @property
    def event_type(self) -> str:
        return "sample.event"


class SampleAggregate(AggregateRoot[str]):
    """Sample aggregate for testing."""

    name: str = Field(default="")
    value: int = Field(default=0)


class TestAggregateRootEvents:
    """Tests for AggregateRoot event methods."""

    def test_add_event(self) -> None:
        """Test adding an event."""
        agg = SampleAggregate(id="agg-1")
        event = SampleEvent(message="test")

        agg.add_event(event)

        assert agg.has_pending_events() is True

    def test_get_pending_events(self) -> None:
        """Test getting pending events."""
        agg = SampleAggregate(id="agg-1")
        event1 = SampleEvent(message="first")
        event2 = SampleEvent(message="second")

        agg.add_event(event1)
        agg.add_event(event2)

        events = agg.get_pending_events()

        assert len(events) == 2
        assert events[0].message == "first"
        assert events[1].message == "second"

    def test_clear_events(self) -> None:
        """Test clearing events."""
        agg = SampleAggregate(id="agg-1")
        agg.add_event(SampleEvent(message="test"))

        cleared = agg.clear_events()

        assert len(cleared) == 1
        assert agg.has_pending_events() is False

    def test_has_pending_events_false(self) -> None:
        """Test has_pending_events returns False when empty."""
        agg = SampleAggregate(id="agg-1")

        assert agg.has_pending_events() is False

    def test_has_pending_events_true(self) -> None:
        """Test has_pending_events returns True when events exist."""
        agg = SampleAggregate(id="agg-1")
        agg.add_event(SampleEvent(message="test"))

        assert agg.has_pending_events() is True


class TestAggregateRootVersion:
    """Tests for AggregateRoot version management."""

    def test_default_version(self) -> None:
        """Test default version is 1."""
        agg = SampleAggregate(id="agg-1")

        assert agg.version == 1

    def test_increment_version(self) -> None:
        """Test incrementing version."""
        agg = SampleAggregate(id="agg-1")

        agg.increment_version()

        assert agg.version == 2

    def test_multiple_increments(self) -> None:
        """Test multiple version increments."""
        agg = SampleAggregate(id="agg-1")

        agg.increment_version()
        agg.increment_version()
        agg.increment_version()

        assert agg.version == 4


class TestAggregateRootApplyEvent:
    """Tests for AggregateRoot.apply_event method."""

    def test_apply_event_adds_to_pending(self) -> None:
        """Test apply_event adds event to pending."""
        agg = SampleAggregate(id="agg-1")
        event = SampleEvent(message="applied")

        agg.apply_event(event)

        events = agg.get_pending_events()
        assert len(events) == 1
        assert events[0].message == "applied"


class TestAggregateRootLifecycle:
    """Tests for AggregateRoot lifecycle methods."""

    def test_mark_updated(self) -> None:
        """Test mark_updated updates timestamp."""
        agg = SampleAggregate(id="agg-1")
        original_updated = agg.updated_at

        agg.mark_updated()

        assert agg.updated_at >= original_updated

    def test_created_at_set(self) -> None:
        """Test created_at is set on creation."""
        agg = SampleAggregate(id="agg-1")

        assert agg.created_at is not None

    def test_updated_at_set(self) -> None:
        """Test updated_at is set on creation."""
        agg = SampleAggregate(id="agg-1")

        assert agg.updated_at is not None
