"""Protocol definitions for the application.

Feature: file-size-compliance-phase2
"""

from core.protocols.base import Identifiable, SoftDeletable, Timestamped
from core.protocols.entities import (
    Auditable,
    DeletableEntity,
    Entity,
    FullEntity,
    TrackedEntity,
    Versionable,
    VersionedEntity,
)
from core.protocols.repository import (
    AsyncRepository,
    CacheProvider,
    Command,
    CommandHandler,
    EventHandler,
    Mapper,
    Query,
    QueryHandler,
    UnitOfWork,
)

__all__ = [
    "AsyncRepository",
    "Auditable",
    "CacheProvider",
    "Command",
    "CommandHandler",
    "DeletableEntity",
    "Entity",
    "EventHandler",
    "FullEntity",
    "Identifiable",
    "Mapper",
    "Query",
    "QueryHandler",
    "SoftDeletable",
    "Timestamped",
    "TrackedEntity",
    "UnitOfWork",
    "Versionable",
    "VersionedEntity",
]
