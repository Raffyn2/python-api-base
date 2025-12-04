# ADR-020: CQRS (Command Query Responsibility Segregation) Adoption

**Status:** Accepted
**Date:** 2025-01-02
**Author:** Architecture Team
**Supersedes:** N/A
**Related:** ADR-019 (Result Pattern)

---

## Context

### Problem Statement

Traditional CRUD-based architectures present challenges for complex enterprise applications:

1. **Mixed Responsibilities:** Same models used for both reading and writing create tight coupling
2. **Optimization Conflicts:** Write models need normalization; read models need denormalization
3. **Scalability Limits:** Reads and writes have different scaling characteristics
4. **Complexity Growth:** Business logic becomes tangled with data access logic
5. **Auditability:** Difficult to track who changed what and why
6. **Domain Modeling:** Difficult to express rich domain behavior in anemic CRUD models

### Current Landscape

The codebase has been evolving from simple CRUD operations to more complex business workflows:

**Before:**
```python
# Simple CRUD
@app.post("/api/v1/users")
async def create_user(user: UserCreate, db: Session):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    return db_user
```

**Pain Points:**
- Business logic mixed with HTTP handling
- No clear separation of concerns
- Difficult to test business logic in isolation
- Hard to add cross-cutting concerns (logging, validation, authorization)
- No audit trail of commands executed

### Requirements

1. **Clear Separation:** Commands (writes) and Queries (reads) should be separate
2. **Scalability:** Read and write paths should scale independently
3. **Testability:** Business logic should be testable in isolation
4. **Auditability:** Every command should be traceable
5. **Flexibility:** Easy to add new commands/queries without affecting existing code
6. **Performance:** Optimize read and write models independently

---

## Decision

We adopt **CQRS (Command Query Responsibility Segregation)** pattern with the following implementation:

### Architecture Overview

```
┌─────────────┐
│   HTTP API  │
└──────┬──────┘
       │
       ├─────────┐
       │         │
       ▼         ▼
 ┌──────────┐  ┌──────────┐
 │ Commands │  │ Queries  │
 └────┬─────┘  └────┬─────┘
      │             │
      ▼             ▼
 ┌─────────────┐  ┌─────────────┐
 │ Command Bus │  │ Query Bus   │
 └──────┬──────┘  └──────┬──────┘
        │                │
        ▼                ▼
 ┌──────────────┐  ┌──────────────┐
 │ Write Model  │  │  Read Model  │
 │ (Domain)     │  │  (DTOs)      │
 └──────┬───────┘  └──────┬───────┘
        │                 │
        └────────┬────────┘
                 ▼
           ┌───────────┐
           │ Database  │
           └───────────┘
```

### Core Components

#### 1. Commands (Write Side)

Commands represent **intentions to change state**:

```python
from dataclasses import dataclass
from core.base.cqrs.command import Command

@dataclass
class CreateUserCommand(Command):
    """Command to create a new user."""
    email: str
    name: str
    password: str

    def __post_init__(self):
        """Validate command data."""
        if not self.email or "@" not in self.email:
            raise ValidationError("Invalid email")
```

#### 2. Command Handlers

Handlers contain business logic:

```python
from application.common.base.use_case import CommandHandler
from core.shared.result import Result, Ok, Err

class CreateUserCommandHandler(CommandHandler[CreateUserCommand, UserDTO]):
    """Handler for CreateUserCommand."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def handle(self, command: CreateUserCommand) -> Result[UserDTO, DomainError]:
        """Execute command."""
        # 1. Validate business rules
        if await self.repository.exists_by_email(command.email):
            return Err(UserAlreadyExistsError(command.email))

        # 2. Create domain entity
        user = User.create(
            email=command.email,
            name=command.name,
            password=command.password
        )

        # 3. Persist
        await self.repository.save(user)

        # 4. Return result
        return Ok(UserDTO.from_entity(user))
```

#### 3. Queries (Read Side)

Queries represent **requests for data**:

```python
from dataclasses import dataclass
from core.base.cqrs.query import Query

@dataclass
class GetUserByIdQuery(Query):
    """Query to get user by ID."""
    user_id: UserId
```

#### 4. Query Handlers

Handlers return optimized read models:

```python
from application.common.base.use_case import QueryHandler

class GetUserByIdQueryHandler(QueryHandler[GetUserByIdQuery, UserDTO]):
    """Handler for GetUserByIdQuery."""

    def __init__(self, read_repository: UserReadRepository):
        self.read_repository = read_repository

    async def handle(self, query: GetUserByIdQuery) -> Result[UserDTO, NotFoundError]:
        """Execute query."""
        user = await self.read_repository.find_by_id(query.user_id)

        if user is None:
            return Err(UserNotFoundError(query.user_id))

        return Ok(user)  # Already a DTO
```

#### 5. Command/Query Bus

Mediator pattern for dispatching:

```python
from application.common.cqrs.command_bus import CommandBus
from application.common.cqrs.query_bus import QueryBus

# Register handlers
command_bus = CommandBus()
command_bus.register(CreateUserCommand, CreateUserCommandHandler(user_repository))

query_bus = QueryBus()
query_bus.register(GetUserByIdQuery, GetUserByIdQueryHandler(user_read_repository))

# Execute
result = await command_bus.execute(CreateUserCommand(email="test@example.com", name="Test"))
user = await query_bus.execute(GetUserByIdQuery(user_id=1))
```

### Implementation Guidelines

#### 1. Commands are Transactional

```python
# Each command is a single transaction
@transaction
async def handle(self, command: CreateUserCommand):
    user = User.create(...)
    await self.repository.save(user)
    await self.event_publisher.publish(UserCreatedEvent(user.id))
    # Commit happens automatically
```

#### 2. Queries are Read-Only

```python
# Queries never modify state
async def handle(self, query: GetUsersQuery):
    # Only SELECT operations
    return await self.read_repository.find_all(query.filters)
```

#### 3. Separate Read/Write Models

```python
# Write Model (Domain Entity)
class User(Entity):
    def __init__(self, id, email, name, password_hash):
        self.id = id
        self.email = email
        self.name = name
        self.password_hash = password_hash

    def change_email(self, new_email):
        # Rich behavior
        if not self._is_valid_email(new_email):
            raise InvalidEmailError()
        self.email = new_email
        self.add_event(UserEmailChangedEvent(self.id, new_email))

# Read Model (DTO)
@dataclass
class UserDTO:
    id: int
    email: str
    name: str
    created_at: datetime
    last_login: datetime | None
    # Optimized for display - no business logic
```

---

## Consequences

### Positive

1. **✅ Clear Separation of Concerns**
   - Commands handle writes
   - Queries handle reads
   - No confusion about responsibility

2. **✅ Independent Scalability**
   - Scale read replicas independently
   - Optimize writes separately
   - Different caching strategies

3. **✅ Optimized Models**
   - Write models: normalized, with business logic
   - Read models: denormalized, optimized for queries
   - No compromises

4. **✅ Better Testability**
   - Test commands in isolation
   - Test queries separately
   - Mock dependencies easily

5. **✅ Audit Trail**
   - Every command is logged
   - Track who did what when
   - Replay commands for debugging

6. **✅ Flexible Evolution**
   - Add new commands without touching queries
   - Add new queries without touching commands
   - Easy to refactor

7. **✅ Middleware Support**
   - Logging middleware
   - Validation middleware
   - Authorization middleware
   - Metrics middleware
   - Retry middleware

8. **✅ Domain-Driven Design**
   - Commands express business intentions
   - Handlers contain business logic
   - Clear ubiquitous language

### Negative

1. **❌ Increased Complexity**
   - More classes and files
   - Learning curve for developers
   - More boilerplate code

   **Mitigation:**
   - Code generators for commands/queries
   - Base classes reduce boilerplate
   - Good documentation and examples

2. **❌ Eventual Consistency**
   - Read models may be stale
   - Need to handle propagation delay

   **Mitigation:**
   - Acceptable for most use cases
   - Can use synchronous updates for critical data
   - Client-side optimistic updates

3. **❌ Duplication**
   - Write and read models duplicate some data
   - Two repositories per aggregate

   **Mitigation:**
   - Acceptable trade-off for flexibility
   - Shared DTOs where appropriate
   - Code generation reduces burden

4. **❌ Infrastructure Overhead**
   - Need command/query buses
   - Need to manage handler registration
   - More moving parts

   **Mitigation:**
   - Dependency injection handles registration
   - Convention-based auto-registration
   - Well-tested infrastructure code

### Neutral

1. **⚖️ Event Sourcing Compatibility**
   - CQRS enables but doesn't require event sourcing
   - Can add later if needed

2. **⚖️ Learning Curve**
   - Different from traditional CRUD
   - Requires mindset shift
   - But leads to clearer architecture

---

## Alternatives Considered

### Alternative 1: Traditional CRUD with Service Layer

**Description:** Keep simple CRUD operations with a service layer for business logic.

```python
class UserService:
    def create_user(self, data: dict) -> User:
        # Business logic here
        user = User(**data)
        self.repository.save(user)
        return user

    def get_user(self, user_id: int) -> User:
        return self.repository.find_by_id(user_id)
```

**Pros:**
- Simple to understand
- Less code
- Standard pattern

**Cons:**
- No clear separation between reads and writes
- Can't optimize independently
- Business logic mixed with data access
- Hard to add cross-cutting concerns
- No audit trail

**Why Rejected:** Doesn't address scalability and complexity concerns for enterprise applications.

---

### Alternative 2: Repository Pattern Only

**Description:** Use repository pattern with separate methods for reads and writes.

```python
class UserRepository:
    # Writes
    def save(self, user: User) -> None: ...
    def delete(self, user_id: int) -> None: ...

    # Reads
    def find_by_id(self, user_id: int) -> User: ...
    def find_all(self, filters: dict) -> list[User]: ...
```

**Pros:**
- Some separation of concerns
- Familiar pattern
- Less infrastructure

**Cons:**
- Still uses same model for read/write
- Can't optimize independently
- No command/query bus for middleware
- No clear representation of business intentions
- Harder to add cross-cutting concerns

**Why Rejected:** Doesn't provide enough separation for complex business logic and scalability needs.

---

### Alternative 3: Event Sourcing

**Description:** Store all changes as events, rebuild state by replaying events.

```python
class UserEventStore:
    def append(self, event: DomainEvent) -> None:
        self.events.append(event)

    def get_events(self, aggregate_id: str) -> list[DomainEvent]:
        return self.events[aggregate_id]

# Rebuild state
user = User()
for event in event_store.get_events(user_id):
    user.apply(event)
```

**Pros:**
- Complete audit trail
- Can rebuild any past state
- Natural fit with CQRS
- Temporal queries

**Cons:**
- Much higher complexity
- Requires event store infrastructure
- Schema evolution challenges
- Snapshots needed for performance
- Overkill for most use cases

**Why Rejected:** Too complex for current requirements. CQRS provides 80% of benefits with 20% of complexity. Can add event sourcing later if needed.

---

### Alternative 4: Vertical Slice Architecture

**Description:** Organize by feature, each feature has its own models, handlers, etc.

```
features/
  user-registration/
    RegisterUserCommand.py
    RegisterUserHandler.py
    RegisterUserController.py
  user-login/
    LoginCommand.py
    LoginHandler.py
    LoginController.py
```

**Pros:**
- High cohesion
- Easy to understand feature scope
- Independent deployment possible

**Cons:**
- Code duplication across features
- Harder to enforce consistency
- Shared logic scattered
- Migration from current structure is difficult

**Why Rejected:** CQRS provides better reusability and consistency. Vertical slices work well within CQRS (each command/query is a slice).

---

## Migration Strategy

### Phase 1: Foundation (Current - Sprint 1)
- [x] Implement command bus
- [x] Implement query bus
- [x] Create base command/query classes
- [x] Create base handler classes
- [x] Add middleware support

### Phase 2: New Features (Sprint 2-3)
- [ ] All new features use CQRS
- [ ] Document patterns and examples
- [ ] Train team on CQRS

### Phase 3: Gradual Migration (Sprint 4-6)
- [ ] Migrate critical endpoints
- [ ] Migrate high-traffic endpoints
- [ ] Keep low-traffic CRUD as-is

### Phase 4: Optimization (Sprint 7-8)
- [ ] Add read replicas
- [ ] Implement read model optimizations
- [ ] Add caching strategies

---

## Examples

### Example 1: Create User Command

```python
# Command
@dataclass
class CreateUserCommand(Command):
    email: str
    name: str
    password: str

# Handler
class CreateUserCommandHandler(CommandHandler[CreateUserCommand, UserDTO]):
    async def handle(self, command: CreateUserCommand) -> Result[UserDTO, DomainError]:
        # Validation
        if await self.repository.exists_by_email(command.email):
            return Err(UserAlreadyExistsError(command.email))

        # Business logic
        user = User.create(
            email=command.email,
            name=command.name,
            password=self.hasher.hash(command.password)
        )

        # Persistence
        await self.repository.save(user)

        # Event
        await self.event_bus.publish(UserCreatedEvent(user.id))

        return Ok(UserDTO.from_entity(user))

# Usage in API
@app.post("/api/v1/users")
async def create_user_endpoint(
    data: CreateUserRequest,
    command_bus: CommandBus = Depends()
):
    result = await command_bus.execute(
        CreateUserCommand(
            email=data.email,
            name=data.name,
            password=data.password
        )
    )

    match result:
        case Ok(user_dto):
            return JSONResponse(status_code=201, content=user_dto.dict())
        case Err(UserAlreadyExistsError()):
            return JSONResponse(status_code=409, content={"error": "User already exists"})
        case Err(error):
            return JSONResponse(status_code=400, content={"error": str(error)})
```

### Example 2: List Users Query

```python
# Query
@dataclass
class ListUsersQuery(Query):
    page: int = 1
    page_size: int = 50
    status: str | None = None

# Handler
class ListUsersQueryHandler(QueryHandler[ListUsersQuery, list[UserDTO]]):
    async def handle(self, query: ListUsersQuery) -> Result[list[UserDTO], QueryError]:
        # Use optimized read model
        users = await self.read_repository.find_all(
            page=query.page,
            page_size=query.page_size,
            status=query.status
        )

        return Ok(users)

# Usage in API
@app.get("/api/v1/users")
async def list_users_endpoint(
    page: int = 1,
    page_size: int = 50,
    status: str | None = None,
    query_bus: QueryBus = Depends()
):
    result = await query_bus.execute(
        ListUsersQuery(
            page=page,
            page_size=page_size,
            status=status
        )
    )

    match result:
        case Ok(users):
            return JSONResponse(content=[u.dict() for u in users])
        case Err(error):
            return JSONResponse(status_code=400, content={"error": str(error)})
```

---

## Monitoring and Success Criteria

### Metrics

1. **Command Throughput**
   - Target: 100 commands/second per instance
   - Measure: `rate(cqrs_command_total[5m])`

2. **Query Throughput**
   - Target: 1000 queries/second per instance
   - Measure: `rate(cqrs_query_total[5m])`

3. **Command Latency**
   - Target: p99 < 500ms
   - Measure: `histogram_quantile(0.99, cqrs_command_duration_seconds)`

4. **Query Latency**
   - Target: p99 < 100ms
   - Measure: `histogram_quantile(0.99, cqrs_query_duration_seconds)`

### Review Schedule

- **1 month:** Review adoption rate and developer feedback
- **3 months:** Assess performance improvements
- **6 months:** Full evaluation and adjustments

---

## References

### Internal
- [Code Review 2025](../code-review-comprehensive-2025-01-02.md)
- [ADR-019 Result Pattern](./ADR-019-result-pattern-adoption-2025.md)
- [Action Items](../ACTION-ITEMS-2025.md)

### External
- [Martin Fowler - CQRS](https://martinfowler.com/bliki/CQRS.html)
- [Greg Young - CQRS Documents](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)
- [Microsoft - CQRS Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- [Axon Framework Guide](https://docs.axoniq.io/reference-guide/)

---

**Last Updated:** 2025-01-02
**Next Review:** 2025-04-01
**Status:** Accepted ✅
