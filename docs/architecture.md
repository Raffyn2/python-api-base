# Architecture

This project follows Clean Architecture principles with a focus on code reuse through Python Generics.

## Layer Diagram

```mermaid
graph TB
    subgraph "Adapters Layer"
        API[API Routes]
        MW[Middleware]
        REPO_IMPL[Repository Implementations]
    end
    
    subgraph "Application Layer"
        UC[Use Cases]
        MAP[Mappers]
        DTO[DTOs]
    end
    
    subgraph "Domain Layer"
        ENT[Entities]
        REPO_INT[Repository Interfaces]
        SPEC[Specifications]
    end
    
    subgraph "Infrastructure Layer"
        DB[Database]
        LOG[Logging]
        CACHE[Cache]
    end
    
    subgraph "Shared/Core"
        GEN[Generic Base Classes]
        CFG[Configuration]
        DI[DI Container]
    end
    
    API --> UC
    UC --> REPO_INT
    UC --> MAP
    REPO_IMPL --> REPO_INT
    REPO_IMPL --> DB
    MW --> API
    GEN --> UC
    GEN --> REPO_INT
    CFG --> DI
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as Middleware
    participant R as Router
    participant UC as UseCase
    participant REPO as Repository
    participant DB as Database
    
    C->>MW: HTTP Request
    MW->>MW: Add Request ID
    MW->>MW: Rate Limit Check
    MW->>R: Forward Request
    R->>UC: Call Use Case
    UC->>REPO: Data Operation
    REPO->>DB: SQL Query
    DB-->>REPO: Result
    REPO-->>UC: Entity
    UC-->>R: Response DTO
    R-->>MW: HTTP Response
    MW->>MW: Add Headers
    MW-->>C: Response
```

## Directory Structure

```
src/my_api/
├── core/                    # Application core
│   ├── config.py           # Pydantic Settings
│   ├── container.py        # DI Container
│   └── exceptions.py       # Domain exceptions
│
├── shared/                  # Reusable generics
│   ├── repository.py       # IRepository[T]
│   ├── use_case.py         # BaseUseCase[T]
│   ├── router.py           # GenericCRUDRouter[T]
│   ├── dto.py              # ApiResponse, PaginatedResponse
│   ├── mapper.py           # IMapper[T, DTO]
│   └── entity.py           # BaseEntity
│
├── domain/                  # Business domain
│   └── entities/           # Domain entities
│       └── item.py
│
├── application/             # Application logic
│   ├── use_cases/          # Business operations
│   └── mappers/            # Entity <-> DTO
│
├── adapters/                # External interfaces
│   ├── api/
│   │   ├── routes/         # FastAPI routers
│   │   └── middleware/     # Request processing
│   └── repositories/       # Data access
│
└── infrastructure/          # Technical concerns
    ├── database/           # DB session, migrations
    └── logging/            # Structured logging
```

## Key Design Decisions

### 1. Generic Base Classes
All CRUD operations are implemented once in generic base classes:
- `IRepository[T, CreateDTO, UpdateDTO]` - Data access interface
- `BaseUseCase[T, CreateDTO, UpdateDTO, ResponseDTO]` - Business logic
- `GenericCRUDRouter[T]` - API endpoints

### 2. Dependency Injection
Using `dependency-injector` for:
- Singleton configuration
- Factory-based session management
- Easy testing with overrides

### 3. Unit of Work Pattern
Transaction management through `IUnitOfWork`:
- Atomic operations across repositories
- Automatic rollback on errors

### 4. Result Pattern
Explicit error handling with `Result[T, E]`:
- `Ok[T]` for success
- `Err[E]` for failures
- No hidden exceptions

### 5. Property-Based Testing
Using Hypothesis for:
- Correctness properties
- Edge case discovery
- Round-trip validation

### 6. Domain Events
Decoupled communication through `EventBus`:
- `DomainEvent` base class for all events
- Async and sync handler support
- Global event bus for cross-cutting concerns

### 7. Resilience Patterns
For external service integration:
- `CircuitBreaker` - Prevents cascading failures
- `retry` decorator - Exponential backoff with jitter
- Configurable thresholds and timeouts

### 8. Code Generation
Entity scaffolding with `scripts/generate_entity.py`:
- Generates entity, mapper, use case, and routes
- Follows project conventions automatically
- Reduces boilerplate and ensures consistency
