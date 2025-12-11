"""Base protocol definitions for entity traits.

Defines fundamental protocols for common entity characteristics like
identification, timestamps, and soft deletion support.

**Feature: file-size-compliance-phase2**
"""

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for entities with an identifier.

    Any class with an `id` attribute satisfies this protocol.
    The id type is Any to support various ID types (str, int, UUID, ULID).
    """

    id: Any


@runtime_checkable
class Timestamped(Protocol):
    """Protocol for entities with timestamp tracking.

    Any class with `created_at` and `updated_at` attributes satisfies this protocol.
    Timestamps should be timezone-aware (UTC recommended).
    """

    created_at: datetime
    updated_at: datetime


@runtime_checkable
class SoftDeletable(Protocol):
    """Protocol for entities supporting soft delete.

    Any class with an `is_deleted` boolean attribute satisfies this protocol.
    Soft-deleted entities should be excluded from normal queries.
    """

    is_deleted: bool


@runtime_checkable
class Named(Protocol):
    """Protocol for entities with a name.

    Any class with a `name` attribute satisfies this protocol.
    """

    name: str
