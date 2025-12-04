"""Event Sourcing pattern implementation.

Provides generic event store, aggregate base class, and event replay
capabilities for building event-sourced systems.

**Feature: code-review-refactoring, Task 1.9: Create __init__.py with re-exports**
**Validates: Requirements 1.2, 2.5**

This module has been refactored from a single file into a package.
All original exports are preserved for backward compatibility.

Original: event_sourcing.py (522 lines)
Refactored: event_sourcing/ package (8 files, ~60-130 lines each)

Usage:
    from infrastructure.db.event_sourcing import (
        Aggregate,
        EventStore,
        InMemoryEventStore,
        SourcedEvent,
    )
"""

# Backward compatible re-exports
from infrastructure.db.event_sourcing.aggregate import Aggregate, AggregateId
from infrastructure.db.event_sourcing.events import EventStream, SourcedEvent
from infrastructure.db.event_sourcing.exceptions import ConcurrencyError
from infrastructure.db.event_sourcing.projections import (
    InMemoryProjection,
    Projection,
)
from infrastructure.db.event_sourcing.repository import EventSourcedRepository
from infrastructure.db.event_sourcing.snapshots import Snapshot
from infrastructure.db.event_sourcing.store import EventStore, InMemoryEventStore

__all__ = [
    # Aggregate
    "Aggregate",
    "AggregateId",
    # Exceptions
    "ConcurrencyError",
    # Repository
    "EventSourcedRepository",
    # Store
    "EventStore",
    "EventStream",
    "InMemoryEventStore",
    "InMemoryProjection",
    # Projections
    "Projection",
    # Snapshots
    "Snapshot",
    # Events
    "SourcedEvent",
]
