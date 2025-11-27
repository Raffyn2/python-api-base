# Implementation Plan

- [x] 1. Set up project structure and core configuration

  - [x] 1.1 Initialize project with pyproject.toml and uv
    - Create pyproject.toml with all dependencies (FastAPI, Pydantic v2, SQLModel, dependency-injector, structlog, hypothesis, etc.)
    - Configure Ruff for linting and formatting
    - Set up pre-commit hooks
    - _Requirements: 17.1, 17.3, 17.4_

  - [x] 1.2 Create directory structure following Clean Architecture
    - Create src/my_api/ with core/, shared/, domain/, application/, adapters/, infrastructure/ directories
    - Create tests/ with unit/, integration/, properties/, factories/ directories
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

  - [x] 1.3 Implement configuration management with Pydantic Settings
    - Create Settings class with nested DatabaseSettings, SecuritySettings, ObservabilitySettings
    - Support environment variables and .env files
    - _Requirements: 12.1, 12.4, 12.5_

  - [x] 1.4 Write property test for configuration validation
    - **Property 18: Missing Config Fails Fast**
    - **Validates: Requirements 12.2**

- [x] 2. Implement shared/core utilities

  - [x] 2.1 Implement datetime utilities with pendulum
    - Create timezone-aware datetime helpers
    - Implement ISO 8601 formatting and parsing
    - _Requirements: 16.1_

  - [x] 2.2 Write property test for datetime formatting
    - **Property 19: DateTime ISO 8601 Formatting**
    - **Validates: Requirements 16.1**

  - [x] 2.3 Implement ID generators (ULID and UUID7)
    - Create type-safe ID generator wrappers
    - Ensure sortability by creation time
    - _Requirements: 16.2_

  - [x] 2.4 Write property test for ID generation
    - **Property 20: ID Generation Uniqueness and Sortability**
    - **Validates: Requirements 16.2**

  - [x] 2.5 Implement password hashing with argon2
    - Create hash and verify functions using passlib
    - _Requirements: 16.3_

  - [x] 2.6 Write property test for password hashing
    - **Property 21: Password Hash Verification**
    - **Validates: Requirements 16.3**

  - [x] 2.7 Implement pagination utilities
    - Create offset and cursor-based pagination helpers
    - _Requirements: 16.4_

  - [x] 2.8 Write property test for pagination utilities
    - **Property 22: Pagination Utility Correctness**
    - **Validates: Requirements 16.4**

  - [x] 2.9 Implement specification pattern for business rules
    - Create Specification base class with and_spec, or_spec, not_spec methods
    - _Requirements: 16.7_

  - [x] 2.10 Write property test for specification pattern
    - **Property 23: Specification Pattern Composition**
    - **Validates: Requirements 16.7**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement generic DTOs and response models

  - [x] 4.1 Create generic ApiResponse model
    - Implement Generic[T] response wrapper with data, message, status_code, timestamp, request_id
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 4.2 Write property test for ApiResponse serialization
    - **Property 1: Generic Response Serialization Completeness**
    - **Validates: Requirements 1.2, 8.3**

  - [x] 4.3 Create generic PaginatedResponse model
    - Implement with items, total, page, size and computed fields (pages, has_next, has_previous)
    - _Requirements: 1.5_

  - [x] 4.4 Write property test for pagination computed fields
    - **Property 3: Pagination Computed Fields Consistency**
    - **Validates: Requirements 1.5**

  - [x] 4.5 Create ProblemDetail model for RFC 7807 errors
    - Implement with type, title, status, detail, instance, errors fields
    - _Requirements: 1.3, 8.2_

  - [x] 4.6 Write property test for validation error format
    - **Property 2: Validation Error Format Compliance**
    - **Validates: Requirements 1.3, 8.2, 9.2**

- [x] 5. Implement base entity and exception hierarchy

  - [x] 5.1 Create BaseEntity with generic ID type
    - Implement with id, created_at, updated_at, is_deleted fields
    - Use ULID for default ID generation
    - _Requirements: 3.1_

  - [x] 5.2 Create exception hierarchy
    - Implement AppException, EntityNotFoundError, ValidationError, BusinessRuleViolationError
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 5.3 Write property test for not found error format
    - **Property 15: Not Found Error Format**
    - **Validates: Requirements 9.1**

  - [x] 5.4 Write property test for business rule violation format
    - **Property 17: Business Rule Violation Format**
    - **Validates: Requirements 9.4**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement generic mapper interface

  - [x] 7.1 Create IMapper generic interface
    - Define to_dto, to_entity, to_dto_list, to_entity_list methods
    - _Requirements: 2.1, 2.2_

  - [x] 7.2 Implement base mapper with automatic field mapping
    - Support matching field names, nested objects, and collections
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 7.3 Write property test for mapper round-trip
    - **Property 4: Mapper Round-Trip Preservation**
    - **Validates: Requirements 2.1, 2.3, 2.4**

  - [x] 7.4 Implement mapper error handling
    - Raise descriptive errors with field context on mapping failures
    - _Requirements: 2.6_

  - [x] 7.5 Write property test for mapper error descriptiveness
    - **Property 5: Mapper Error Descriptiveness**
    - **Validates: Requirements 2.6**

- [x] 8. Implement generic repository interface

  - [x] 8.1 Create IRepository generic interface
    - Define async CRUD methods: get_by_id, get_all, create, update, delete, create_many, exists
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 8.2 Implement in-memory repository for testing
    - Create InMemoryRepository implementing IRepository
    - _Requirements: 14.3_

  - [x] 8.3 Write property test for repository create-get round-trip
    - **Property 6: Repository Create-Get Round-Trip**
    - **Validates: Requirements 3.3, 3.4**

  - [x] 8.4 Write property test for repository update persistence
    - **Property 7: Repository Update Persistence**
    - **Validates: Requirements 3.5**

  - [x] 8.5 Write property test for repository soft delete
    - **Property 8: Repository Soft Delete Behavior**
    - **Validates: Requirements 3.6**

  - [x] 8.6 Write property test for repository pagination bounds
    - **Property 9: Repository Pagination Bounds**
    - **Validates: Requirements 3.2**

  - [x] 8.7 Write property test for bulk create atomicity
    - **Property 10: Bulk Create Atomicity**
    - **Validates: Requirements 3.7**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement generic use case layer

  - [x] 10.1 Create BaseUseCase generic class
    - Implement CRUD operations delegating to repository
    - Use mapper for DTO conversions
    - _Requirements: 4.1, 4.2, 4.3, 4.6_

  - [x] 10.2 Implement use case validation and error handling
    - Raise domain-specific exceptions with context
    - _Requirements: 4.5_

  - [x] 10.3 Write unit tests for use case operations
    - Test CRUD delegation and mapper integration
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 11. Implement database infrastructure

  - [x] 11.1 Set up async SQLAlchemy session factory
    - Configure asyncpg connection pooling
    - Create async context managers for transactions
    - _Requirements: 13.1, 13.3_

  - [x] 11.2 Create SQLModel base repository implementation
    - Implement SQLModelRepository extending IRepository
    - _Requirements: 13.2, 3.8_

  - [x] 11.3 Write integration tests for SQLModel repository

    - Test CRUD operations with real database (PostgreSQL via Docker)
    - _Requirements: 14.2_

- [x] 12. Implement generic CRUD router

  - [x] 12.1 Create GenericCRUDRouter class
    - Generate list, detail, create, update, delete endpoints
    - Use class-based views pattern
    - _Requirements: 5.1, 5.8_

  - [x] 12.2 Write property test for POST endpoint

    - **Property 11: Endpoint POST Returns 201 with Entity**
    - **Validates: Requirements 5.2**


  - [x] 12.3 Write property test for GET list endpoint
    - **Property 12: Endpoint GET List Returns Paginated Response**
    - **Validates: Requirements 5.3**


  - [x] 12.4 Write property test for GET detail endpoint
    - **Property 13: Endpoint GET Detail Returns Entity or 404**

    - **Validates: Requirements 5.4**

  - [x] 12.5 Write property test for DELETE endpoint
    - **Property 14: Endpoint DELETE Returns 204 or 404**
    - **Validates: Requirements 5.6**

  - [x] 12.6 Implement bulk operation endpoints
    - Add batch create, update, delete endpoints
    - _Requirements: 5.7_

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Implement error handling middleware

  - [x] 14.1 Create global exception handlers
    - Handle AppException, ValidationError, and unhandled exceptions

    - Return RFC 7807 Problem Details format
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 14.2 Write property test for internal error concealment
    - **Property 16: Internal Error Concealment**
    - **Validates: Requirements 9.3**

  - [x] 14.3 Implement authentication error handler
    - Return 401 with WWW-Authenticate header
    - _Requirements: 9.5_

  - [x] 14.4 Implement rate limit error handler
    - Return 429 with Retry-After header
    - _Requirements: 9.6_

- [x] 15. Implement dependency injection container

  - [x] 15.1 Create DI container with dependency-injector
    - Configure providers for repositories, mappers, use cases
    - Wire to FastAPI routes
    - _Requirements: 6.1, 6.2, 6.4, 6.6_


  - [x] 15.2 Implement lifecycle management
    - Add startup and shutdown hooks
    - _Requirements: 6.5_

  - [x] 15.3 Write unit tests for DI container
    - Test dependency resolution and override capability
    - _Requirements: 6.3_

- [x] 16. Implement example Item entity and endpoints

  - [x] 16.1 Create Item domain entity and SQLModel
    - Implement ItemBase, Item, ItemCreate, ItemUpdate, ItemResponse
    - _Requirements: 1.6, 1.7_

  - [x] 16.2 Create ItemMapper implementation
    - Map between Item entity and ItemResponse DTO
    - _Requirements: 2.1, 2.5_

  - [x] 16.3 Create ItemUseCase extending BaseUseCase
    - Add any item-specific business logic
    - _Requirements: 4.3, 4.4_


  - [x] 16.4 Create Item routes using GenericCRUDRouter
    - Wire up /items endpoints
    - _Requirements: 5.1_

  - [x] 16.5 Write integration tests for Item endpoints
    - Test full CRUD flow
    - _Requirements: 14.2_

- [x] 17. Implement observability stack

  - [x] 17.1 Configure structlog for JSON logging
    - Set up processors for trace correlation
    - Implement PII redaction
    - _Requirements: 10.2, 11.3_

  - [x] 17.2 Set up OpenTelemetry tracing
    - Configure span context propagation

    - _Requirements: 10.1_

  - [x] 17.3 Implement health check endpoints
    - Create /health/live and /health/ready endpoints
    - _Requirements: 10.4_

  - [x] 17.4 Write unit tests for health endpoints
    - Test liveness and readiness responses
    - _Requirements: 10.4_

- [x] 18. Implement security middleware

  - [x] 18.1 Configure CORS middleware
    - Support configurable origins, methods, headers
    - _Requirements: 11.1_

  - [x] 18.2 Implement rate limiting with slowapi
    - Configure per-client rate limits
    - _Requirements: 11.2_

  - [x] 18.3 Add security headers middleware
    - Include standard security headers
    - _Requirements: 11.4_

  - [x] 18.4 Implement input sanitization
    - Sanitize input to prevent injection attacks
    - _Requirements: 11.5_

- [x] 19. Set up API documentation

  - [x] 19.1 Configure Swagger UI and ReDoc
    - Enable /docs and /redoc endpoints
    - _Requirements: 15.1, 15.2_

  - [x] 19.2 Add request/response examples to models
    - Use json_schema_extra for examples
    - _Requirements: 15.3_

  - [x] 19.3 Configure OpenAPI spec
    - Set up versioning and tags
    - _Requirements: 15.5_


- [x] 20. Create FastAPI application entry point

  - [x] 20.1 Implement main.py with app factory
    - Wire all routers, middleware, and exception handlers
    - Initialize DI container
    - _Requirements: 6.4, 6.6_

  - [x] 20.2 Write integration tests for application startup
    - Test app initialization and health endpoints
    - _Requirements: 12.2_

- [x] 21. Set up testing infrastructure

  - [x] 21.1 Create pytest configuration and fixtures
    - Set up async test client, database fixtures
    - _Requirements: 14.1, 14.2_



  - [x] 21.2 Create polyfactory factories for test data
    - Generate test entities automatically
    - _Requirements: 14.1_

  - [x] 21.3 Create hypothesis strategies for property tests
    - Define strategies for entities, DTOs, pagination
    - _Requirements: 14.5_

  - [x] 21.4 Create mock repository factories
    - Support configurable mock behavior
    - _Requirements: 14.4_

- [x] 22. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
