"""Core base classes for the application.

Provides foundational patterns:
- Domain: Entity, Aggregate, ValueObject
- Events: DomainEvent, IntegrationEvent
- Repository: IRepository, InMemoryRepository
- CQRS: Command, Query
- Patterns: Result, Specification, Validation

**Feature: architecture-restructuring-2025**
"""

# Domain building blocks
# CQRS
from core.base.cqrs import BaseCommand, BaseQuery
from core.base.domain import (
    AggregateRoot,
    AuditableEntity,
    AuditableVersionedEntity,
    BaseEntity,
    BaseValueObject,
    ULIDEntity,
    VersionedEntity,
)

# Events
from core.base.events import (
    DomainEvent,
    EntityCreatedEvent,
    EntityDeletedEvent,
    EntityUpdatedEvent,
    EventBus,
    IntegrationEvent,
)

# Patterns
from core.base.patterns import (
    AndSpecification,
    AttributeSpecification,
    ChainedValidator,
    CompositeValidator,
    # Pagination
    CursorPage,
    CursorPagination,
    Err,
    FalseSpecification,
    FieldError,
    NotSpecification,
    Ok,
    OrSpecification,
    PredicateSpecification,
    PredicateValidator,
    RangeValidator,
    # Result
    Result,
    # Specification
    Specification,
    TrueSpecification,
    # UoW
    UnitOfWork,
    ValidationError,
    # Validation
    Validator,
    collect_results,
    validate_all,
)

# Repository
from core.base.repository import (
    InMemoryRepository,
    IRepository,
)

__all__ = [
    "AggregateRoot",
    "AndSpecification",
    "AttributeSpecification",
    "AuditableEntity",
    "AuditableVersionedEntity",
    # CQRS
    "BaseCommand",
    # Domain
    "BaseEntity",
    "BaseQuery",
    "BaseValueObject",
    "ChainedValidator",
    "CompositeValidator",
    # Pagination
    "CursorPage",
    "CursorPagination",
    # Events
    "DomainEvent",
    "EntityCreatedEvent",
    "EntityDeletedEvent",
    "EntityUpdatedEvent",
    "Err",
    "EventBus",
    "FalseSpecification",
    "FieldError",
    # Repository
    "IRepository",
    "InMemoryRepository",
    "IntegrationEvent",
    "NotSpecification",
    "Ok",
    "OrSpecification",
    "PredicateSpecification",
    "PredicateValidator",
    "RangeValidator",
    # Result
    "Result",
    # Specification
    "Specification",
    "TrueSpecification",
    "ULIDEntity",
    # UoW
    "UnitOfWork",
    "ValidationError",
    # Validation
    "Validator",
    "VersionedEntity",
    "collect_results",
    "validate_all",
]
