"""Tests for infrastructure/db/event_sourcing/events.py - Event sourcing events."""

from dataclasses import dataclass, field
from datetime import datetime

import pytest

from src.infrastructure.db.event_sourcing.events import EventStream, SourcedEvent


@dataclass(frozen=True, slots=True)
class UserCreatedEvent(SourcedEvent):
    """Test event for user creation."""

    username: str = ""
    email: str = ""


class TestSourcedEvent:
    """Tests for SourcedEvent class."""

    def test_auto_generates_event_id(self):
        event = SourcedEvent()
        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_event_id_is_unique(self):
        event1 = SourcedEvent()
        event2 = SourcedEvent()
        assert event1.event_id != event2.event_id

    def test_aggregate_id_default_empty(self):
        event = SourcedEvent()
        assert event.aggregate_id == ""

    def test_version_default_zero(self):
        event = SourcedEvent()
        assert event.version == 0

    def test_timestamp_is_set(self):
        event = SourcedEvent()
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_metadata_default_empty_dict(self):
        event = SourcedEvent()
        assert event.metadata == {}

    def test_custom_aggregate_id(self):
        event = SourcedEvent(aggregate_id="agg-123")
        assert event.aggregate_id == "agg-123"

    def test_custom_version(self):
        event = SourcedEvent(version=5)
        assert event.version == 5

    def test_custom_metadata(self):
        event = SourcedEvent(metadata={"key": "value"})
        assert event.metadata == {"key": "value"}

    def test_event_type_returns_class_name(self):
        event = SourcedEvent()
        assert event.event_type == "SourcedEvent"

    def test_is_immutable(self):
        event = SourcedEvent()
        with pytest.raises(AttributeError):
            event.aggregate_id = "new-id"


class TestSourcedEventSubclass:
    """Tests for SourcedEvent subclasses."""

    def test_subclass_event_type(self):
        event = UserCreatedEvent(username="test", email="test@example.com")
        assert event.event_type == "UserCreatedEvent"

    def test_subclass_inherits_fields(self):
        event = UserCreatedEvent(
            aggregate_id="user-123",
            version=1,
            username="testuser",
            email="test@example.com",
        )
        assert event.aggregate_id == "user-123"
        assert event.version == 1
        assert event.username == "testuser"
        assert event.email == "test@example.com"

    def test_subclass_is_immutable(self):
        event = UserCreatedEvent(username="test", email="test@example.com")
        with pytest.raises(AttributeError):
            event.username = "changed"


class TestEventStream:
    """Tests for EventStream class."""

    def test_init_with_aggregate_id(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        assert stream.aggregate_id == "agg-123"

    def test_init_with_aggregate_type(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        assert stream.aggregate_type == "User"

    def test_events_default_empty_list(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        assert stream.events == []

    def test_version_default_zero(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        assert stream.version == 0

    def test_created_at_is_set(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        assert stream.created_at is not None
        assert isinstance(stream.created_at, datetime)

    def test_updated_at_is_set(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        assert stream.updated_at is not None
        assert isinstance(stream.updated_at, datetime)


class TestEventStreamAppend:
    """Tests for EventStream.append method."""

    def test_append_adds_event(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        event = SourcedEvent(aggregate_id="agg-123")
        stream.append(event)
        assert len(stream.events) == 1
        assert stream.events[0] == event

    def test_append_updates_version(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        stream.append(SourcedEvent())
        assert stream.version == 1

    def test_append_multiple_events(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        stream.append(SourcedEvent())
        stream.append(SourcedEvent())
        stream.append(SourcedEvent())
        assert len(stream.events) == 3
        assert stream.version == 3

    def test_append_updates_updated_at(self):
        stream = EventStream(aggregate_id="agg-123", aggregate_type="User")
        original = stream.updated_at
        stream.append(SourcedEvent())
        assert stream.updated_at >= original


class TestEventStreamWithEvents:
    """Tests for EventStream with pre-populated events."""

    def test_init_with_events(self):
        events = [SourcedEvent(), SourcedEvent()]
        stream = EventStream(
            aggregate_id="agg-123",
            aggregate_type="User",
            events=events,
        )
        assert len(stream.events) == 2

    def test_init_with_version(self):
        stream = EventStream(
            aggregate_id="agg-123",
            aggregate_type="User",
            version=5,
        )
        assert stream.version == 5
