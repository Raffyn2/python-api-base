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
    AuditableULIDEntity,
    AuditableVersionedEntity,
    AuditLogId,
    BaseEntity,
    BaseValueObject,
    EntityId,
    ItemId,
    RoleId,
    ULIDEntity,
    UserId,
    VersionedEntity,
    VersionedULIDEntity,
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
    AlternativeValidator,
    AndSpecification,
    AttributeSpecification,
    BaseUseCase,
    ChainedValidator,
    CompositeSpecification,
    CompositeValidator,
    # Pagination
    CursorPage,
    CursorPagination,
    Err,
    FalseSpecification,
    FieldError,
    NotEmptyValidator,
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
    err,
    ok,
    result_from_dict,
    try_catch,
    try_catch_async,
    validate_all,
)

# Repository
from core.base.repository import (
    InMemoryRepository,
    IRepository,
)

__all__ = [
    "AggregateRoot",
    "AlternativeValidator",
    "AndSpecification",
    "AttributeSpecification",
    "AuditLogId",
    "AuditableEntity",
    "AuditableULIDEntity",
    "AuditableVersionedEntity",
    # CQRS
    "BaseCommand",
    # Domain
    "BaseEntity",
    "BaseQuery",
    # UseCase
    "BaseUseCase",
    "BaseValueObject",
    "ChainedValidator",
    "CompositeSpecification",
    "CompositeValidator",
    # Pagination
    "CursorPage",
    "CursorPagination",
    # Events
    "DomainEvent",
    "EntityCreatedEvent",
    "EntityDeletedEvent",
    # Typed IDs
    "EntityId",
    "EntityUpdatedEvent",
    "Err",
    "EventBus",
    "FalseSpecification",
    "FieldError",
    # Repository
    "IRepository",
    "InMemoryRepository",
    "IntegrationEvent",
    "ItemId",
    "NotEmptyValidator",
    "NotSpecification",
    "Ok",
    "OrSpecification",
    "PredicateSpecification",
    "PredicateValidator",
    "RangeValidator",
    # Result
    "Result",
    "RoleId",
    # Specification
    "Specification",
    "TrueSpecification",
    "ULIDEntity",
    # UoW
    "UnitOfWork",
    "UserId",
    "ValidationError",
    # Validation
    "Validator",
    "VersionedEntity",
    "VersionedULIDEntity",
    "collect_results",
    "err",
    "ok",
    "result_from_dict",
    "try_catch",
    "try_catch_async",
    "validate_all",
]
