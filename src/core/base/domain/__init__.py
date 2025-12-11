"""Domain building blocks.

Provides DDD tactical patterns:
- Entity: Base entity with identity
- AggregateRoot: Aggregate boundary with events
- ValueObject: Immutable value types
- EntityId: Typed ID value objects with ULID validation
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
from core.base.domain.value_object import (
    AuditLogId,
    BaseValueObject,
    EntityId,
    ItemId,
    RoleId,
    UserId,
)

__all__ = [
    # Aggregate
    "AggregateRoot",
    "AuditLogId",
    # Entity
    "AuditableEntity",
    "AuditableULIDEntity",
    "AuditableVersionedEntity",
    "BaseEntity",
    # Value Object
    "BaseValueObject",
    # Typed IDs
    "EntityId",
    "ItemId",
    "RoleId",
    "ULIDEntity",
    "UserId",
    "VersionedEntity",
    "VersionedULIDEntity",
]
