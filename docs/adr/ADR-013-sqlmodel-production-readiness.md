# ADR-013: SQLModel Production Readiness

## Status

**Accepted**

## Context

SQLModel is a library that combines SQLAlchemy and Pydantic, providing a unified way to define database models and API schemas. While SQLModel offers developer experience benefits, there are considerations for production use:

**Current SQLModel Limitations (as of 2025):**
1. Limited complex query support compared to raw SQLAlchemy
2. No native support for database migrations (relies on Alembic)
3. Performance overhead from Pydantic validation layer
4. Async support still maturing
5. Limited TypeVar/Generic support in some edge cases

**Project Context:**
- The codebase uses PEP 695 generics extensively
- Repository pattern with `AsyncRepository[T, CreateDTO, UpdateDTO]`
- Need for type-safe database operations
- Existing SQLAlchemy infrastructure

## Decision

We will use **SQLModel with SQLAlchemy fallback** strategy:

### 1. SQLModel for Simple CRUD

Use SQLModel for straightforward entity definitions and basic CRUD operations:

```python
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
```

### 2. SQLAlchemy for Complex Queries

Fall back to SQLAlchemy Core or ORM for:
- Complex joins
- Window functions
- CTEs (Common Table Expressions)
- Bulk operations with performance requirements

```python
from sqlalchemy import select, func

# Complex query using SQLAlchemy
stmt = (
    select(User, func.count(Order.id))
    .join(Order)
    .group_by(User.id)
    .having(func.count(Order.id) > 5)
)
```

### 3. Repository Abstraction

The `SQLModelRepository[T, CreateT, UpdateT, IdType]` provides:
- Unified interface regardless of backend
- Easy testing with in-memory implementations
- Type safety through generics

```python
class SQLModelRepository[T: SQLModel, CreateT, UpdateT, IdType = str]:
    async def get_by_id(self, entity_id: IdType) -> T | None: ...
    async def create(self, data: CreateT) -> T: ...
    async def update(self, entity_id: IdType, data: UpdateT) -> T | None: ...
    async def delete(self, entity_id: IdType) -> bool: ...
```

### 4. Migration Strategy

Use Alembic for database migrations with SQLModel models:

```python
# alembic/env.py
from sqlmodel import SQLModel
target_metadata = SQLModel.metadata
```

### 5. Performance Guidelines

- **Bulk operations**: Use SQLAlchemy Core for >100 records
- **Read-heavy endpoints**: Use read replicas and caching
- **Complex reports**: Use raw SQL or views

## Consequences

### Positive

- **Developer Experience**: SQLModel's Pydantic integration simplifies DTOs
- **Type Safety**: Full IDE support and runtime validation
- **Flexibility**: Can escalate to SQLAlchemy when needed
- **Testability**: Repository pattern enables easy mocking

### Negative

- **Learning Curve**: Team must understand both SQLModel and SQLAlchemy
- **Dual Dependency**: Maintaining compatibility with both libraries
- **Performance Monitoring**: Need to identify when SQLModel overhead matters

### Neutral

- **Migration Complexity**: Same as pure SQLAlchemy (Alembic)
- **Documentation**: Must document when to use each approach

## Implementation Checklist

- [x] `SQLModelRepository` generic implementation
- [x] Repository protocol definition (`AsyncRepository`)
- [x] Alembic migration setup
- [x] Connection pooling configuration
- [ ] Read replica support
- [ ] Query performance monitoring
- [ ] Bulk operation utilities

## References

- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- ADR-005: Repository Pattern

## Revision History

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-03 | 1.0 | Initial decision |
