"""Domain building blocks.

Provides DDD tactical patterns:
- Entity: Base entity with identity
- AggregateRoot: Aggregate boundary with events
- ValueObject: Immutable value types
"""

from core.base.domain.aggregate_root import AggregateRoot
from core.base.domain.entity import (
    AuditableEntity,
    AuditableULIDEntity,
    AuditableVersionedEntity,
    BaseEntity,
    ULIDEntity,
    VersionedEntity,
    VersionedULIDEntity,
)
from core.base.domain.value_object import BaseValueObject

__all__ = [
    # Aggregate
    "AggregateRoot",
    "AuditableEntity",
    "AuditableULIDEntity",
    "AuditableVersionedEntity",
    # Entity
    "BaseEntity",
    # Value Object
    "BaseValueObject",
    "ULIDEntity",
    "VersionedEntity",
    "VersionedULIDEntity",
]
