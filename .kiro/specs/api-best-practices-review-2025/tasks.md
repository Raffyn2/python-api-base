# Implementation Plan

## Phase 1: JWT Security (RS256)

- [ ] 1. Implement JWT RS256 Authentication
  - [ ] 1.1 Create RSA key pair generation utility
    - Generate 2048-bit RSA key pair
    - Store private key securely (environment variable or vault)
    - Implement key ID (kid) generation
    - _Requirements: 2.1, 20.1_
  - [ ] 1.2 Implement JWTServiceRS256 class
    - Create access token with RS256 algorithm
    - Create refresh token with separate signing
    - Include kid in token header
    - _Requirements: 2.1, 20.1, 20.5_
  - [ ] 1.3 Write property test for JWT RS256 algorithm
    - **Property 1: JWT RS256 Algorithm Enforcement**
    - **Validates: Requirements 2.1, 20.1**
  - [ ] 1.4 Implement JWKS endpoint at /.well-known/jwks.json
    - Expose public key in JWK format
    - Include kid, kty, alg, use, n, e fields
    - _Requirements: 20.2_
  - [ ] 1.5 Write property test for JWT round-trip
    - **Property 2: JWT Round-Trip Consistency**
    - **Validates: Requirements 7.2**
  - [ ] 1.6 Implement key rotation support
    - Support multiple keys in JWKS
    - Validate tokens against all keys in set
    - Remove old keys after grace period
    - _Requirements: 20.3, 20.6_
  - [ ] 1.7 Write property test for key rotation
    - **Property 3: JWT Key Rotation Backward Compatibility**
    - **Validates: Requirements 20.3**
  - [ ] 1.8 Write property test for kid validation
    - **Property 4: JWT Kid Validation**
    - **Validates: Requirements 20.4**

- [ ] 2. Checkpoint - Ensure all JWT tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 2: Redis Cache with TTL Jitter

- [ ] 3. Implement Redis Cache with Jitter
  - [ ] 3.1 Create RedisCacheWithJitter class
    - Implement _apply_jitter method (5-15% random jitter)
    - Implement set method with jittered TTL
    - Implement get method with deserialization
    - _Requirements: 6.2, 22.1_
  - [ ] 3.2 Write property test for TTL jitter range
    - **Property 9: Cache TTL Jitter Range**
    - **Validates: Requirements 22.1**
  - [ ] 3.3 Implement distributed locking for cache stampede prevention
    - Use Redis SETNX for lock acquisition
    - Implement get_or_compute with lock
    - Handle lock timeout and retry
    - _Requirements: 6.5, 22.3_
  - [ ] 3.4 Write property test for stampede prevention
    - **Property 10: Cache Stampede Prevention**
    - **Validates: Requirements 22.3**
  - [ ] 3.5 Implement probabilistic early expiration
    - Calculate probability based on remaining TTL
    - Trigger recomputation before expiration
    - _Requirements: 22.4_

- [ ] 4. Checkpoint - Ensure all cache tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 3: Pydantic V2 Performance

- [ ] 5. Implement Pydantic V2 Performance Patterns
  - [ ] 5.1 Create TypeAdapter instances for common types
    - Define TypeAdapter for ItemDTO list
    - Define TypeAdapter for PedidoDTO list
    - Ensure single instantiation (module level)
    - _Requirements: 19.2_
  - [ ] 5.2 Update DTOs to use model_validate_json
    - Replace model_validate(json.loads()) with model_validate_json()
    - Update request handlers to use direct JSON validation
    - _Requirements: 19.1_
  - [ ] 5.3 Write property test for JSON validation equivalence
    - **Property 8: Pydantic JSON Validation Equivalence**
    - **Validates: Requirements 19.1**
  - [ ] 5.4 Implement computed_field with caching
    - Add @computed_field decorator to calculated properties
    - Use @lru_cache for expensive computations
    - _Requirements: 19.5_
  - [ ] 5.5 Use TypedDict for simple nested structures
    - Replace simple nested BaseModel with TypedDict
    - Update serialization to handle TypedDict
    - _Requirements: 19.3_
  - [ ] 5.6 Implement FailFast for sequence validation
    - Add FailFast annotation to list fields
    - Update error handling for early failures
    - _Requirements: 19.6_

- [ ] 6. Checkpoint - Ensure all Pydantic tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: API Idempotency

- [ ] 7. Implement Idempotency Handler
  - [ ] 7.1 Create IdempotencyHandler class
    - Implement idempotency key storage in Redis
    - Implement request hash computation
    - Configure TTL (24-48 hours)
    - _Requirements: 23.1, 23.2_
  - [ ] 7.2 Implement execute_idempotent method
    - Check for existing idempotency record
    - Execute operation if new key
    - Return cached response if duplicate
    - _Requirements: 23.3_
  - [ ] 7.3 Write property test for idempotency replay
    - **Property 11: Idempotency Key Replay**
    - **Validates: Requirements 23.1, 23.3**
  - [ ] 7.4 Implement conflict detection
    - Compare request hash for same key
    - Return 422 error if hash differs
    - _Requirements: 23.4_
  - [ ] 7.5 Write property test for conflict detection
    - **Property 12: Idempotency Key Conflict Detection**
    - **Validates: Requirements 23.4**
  - [ ] 7.6 Create idempotency middleware
    - Extract Idempotency-Key header
    - Wrap POST/PATCH handlers with idempotency
    - Add X-Idempotent-Replayed header to responses
    - _Requirements: 23.1, 23.5_

- [ ] 8. Checkpoint - Ensure all idempotency tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 5: Health Checks and Graceful Shutdown

- [ ] 9. Implement Health Check System
  - [ ] 9.1 Create HealthCheckService class
    - Implement liveness check (simple 200)
    - Implement readiness check (verify dependencies)
    - Implement startup probe (wait for dependencies)
    - _Requirements: 24.1, 24.2, 24.3_
  - [ ] 9.2 Create health check endpoints
    - GET /health/live for liveness
    - GET /health/ready for readiness
    - Include dependency status in response
    - _Requirements: 24.7_
  - [ ] 9.3 Write unit tests for health checks
    - Test liveness returns 200
    - Test readiness fails without database
    - Test readiness fails without Redis
    - _Requirements: 24.1, 24.2_
  - [ ] 9.4 Implement graceful shutdown
    - Handle SIGTERM signal
    - Stop accepting new requests
    - Wait for in-flight requests to complete
    - Close database connections
    - Flush metrics
    - _Requirements: 24.4, 24.5, 24.6_

- [ ] 10. Checkpoint - Ensure all health check tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 6: RBAC and Specifications

- [ ] 11. Validate RBAC Implementation
  - [ ] 11.1 Review existing RBAC implementation
    - Verify role hierarchy (admin > editor > viewer)
    - Verify permission composition
    - Verify example_viewer, example_editor, example_admin roles
    - _Requirements: 2.5, 28.5_
  - [ ] 11.2 Write property test for permission composition
    - **Property 5: RBAC Permission Composition**
    - **Validates: Requirements 7.3**

- [ ] 12. Validate Specification Pattern
  - [ ] 12.1 Review existing specification implementation
    - Verify ItemExampleActiveSpec, ItemExampleCategorySpec
    - Verify PedidoPendingSpec, PedidoTenantSpec
    - Verify composition methods (and_spec, or_spec, not_spec)
    - _Requirements: 5.5, 26.4_
  - [ ] 12.2 Write property test for specification laws
    - **Property 7: Specification Composition Laws**
    - **Validates: Requirements 7.5**
  - [ ] 12.3 Write property test for specification filtering
    - **Property 14: Specification Filtering Correctness**
    - **Validates: Requirements 26.4, 28.3**

- [ ] 13. Checkpoint - Ensure all RBAC and specification tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 7: Repository and CRUD Consistency

- [ ] 14. Validate Repository Implementation
  - [ ] 14.1 Review ItemExampleRepository
    - Verify async CRUD operations
    - Verify soft delete implementation
    - Verify specification query support
    - _Requirements: 5.2, 26.3_
  - [ ] 14.2 Review PedidoExampleRepository
    - Verify async CRUD operations
    - Verify tenant filtering
    - Verify status transitions
    - _Requirements: 5.2, 26.3_
  - [ ] 14.3 Write property test for CRUD consistency
    - **Property 6: Repository CRUD Consistency**
    - **Validates: Requirements 7.4**
  - [ ] 14.4 Write property test for ItemExample CRUD via API
    - **Property 13: ItemExample CRUD Consistency**
    - **Validates: Requirements 26.1, 28.1**

- [ ] 15. Checkpoint - Ensure all repository tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 8: SQLModel Production Readiness

- [ ] 16. Document SQLModel Risks and Fallbacks
  - [ ] 16.1 Create ADR for SQLModel usage
    - Document bus factor risk (single maintainer)
    - Document fallback strategy to pure SQLAlchemy
    - Document when to use SQLAlchemy directly
    - _Requirements: 21.1_
  - [ ] 16.2 Review complex queries for SQLAlchemy fallback
    - Identify queries using SQLModel-specific features
    - Implement fallback using SQLAlchemy 2.0 syntax
    - _Requirements: 21.2, 21.3_
  - [ ] 16.3 Verify Alembic compatibility
    - Test migrations with SQLModel models
    - Ensure proper async session handling
    - _Requirements: 21.5, 21.6_

## Phase 9: Docker Integration Testing

- [ ] 17. Setup Docker Integration Tests
  - [ ] 17.1 Create integration test fixtures
    - Setup docker-compose for tests
    - Create API client fixture
    - Create database cleanup fixture
    - _Requirements: 27.1, 27.2_
  - [ ] 17.2 Implement ItemExample E2E tests
    - Test POST /api/v1/items creates item
    - Test GET /api/v1/items/{id} returns item
    - Test PATCH /api/v1/items/{id} updates item
    - Test DELETE /api/v1/items/{id} soft deletes
    - _Requirements: 28.1, 28.3_
  - [ ] 17.3 Implement PedidoExample E2E tests
    - Test POST /api/v1/pedidos creates pedido
    - Test POST /api/v1/pedidos/{id}/items adds item
    - Test POST /api/v1/pedidos/{id}/confirm confirms pedido
    - _Requirements: 28.2, 28.4_
  - [ ] 17.4 Verify Swagger UI and ReDoc
    - Test /docs endpoint accessible
    - Test /redoc endpoint accessible
    - Verify OpenAPI schema generation
    - _Requirements: 27.3_

- [ ] 18. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

