# Implementation Plan

## Architecture Review Validation Tasks

- [x] 1. Validate existing property-based tests coverage

  - [x] 1.1 Review JWT token round-trip property test


    - Verify `tests/properties/test_jwt_properties.py` covers token creation and verification
    - Ensure minimum 100 iterations configured
    - **Property 1: JWT Token Round-Trip**
    - _Requirements: 2.1, 2.2_
  - [x] 1.2 Review RBAC permission composition property test


    - Verify `tests/properties/test_rbac_properties.py` covers role permission union
    - **Property 2: RBAC Permission Composition**
    - _Requirements: 2.3_
  - [x] 1.3 Review circuit breaker state transition property test


    - Verify state machine transitions in property tests
    - **Property 3: Circuit Breaker State Transitions**
    - _Requirements: 3.1_
  - [x] 1.4 Review repository CRUD consistency property test


    - Verify `tests/properties/test_repository_properties.py` covers create/retrieve round-trip
    - **Property 4: Repository CRUD Consistency**
    - _Requirements: 1.4_
  - [x] 1.5 Review cache invalidation property test


    - Verify `tests/properties/test_caching_properties.py` covers cache consistency
    - **Property 5: Cache Invalidation**
    - _Requirements: 3.7_
  - [x] 1.6 Review rate limiter fairness property test


    - Verify rate limiting behavior in property tests
    - **Property 6: Rate Limiter Fairness**
    - _Requirements: 2.4_
  - [x] 1.7 Review security headers presence property test


    - Verify `tests/properties/test_security_headers_properties.py` covers all required headers
    - **Property 7: Security Headers Presence**
    - _Requirements: 2.5_
  - [x] 1.8 Review error response format property test


    - Verify `tests/properties/test_error_handler_properties.py` covers RFC 7807 format
    - **Property 8: Error Response Format**
    - _Requirements: 5.4_

- [x] 2. Checkpoint - Ensure all existing tests pass



  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement token revocation with Redis integration



  - [x] 3.1 Create Redis token store implementation

    - Implement `RedisTokenStore` class in `src/my_api/infrastructure/auth/token_store.py`
    - Add `revoke(jti, ttl)` and `is_revoked(jti)` async methods
    - Configure Redis connection from environment variables
    - _Requirements: 2.10_
  - [x] 3.2 Write property test for token revocation


    - Test that revoked tokens are rejected on verification
    - Test TTL expiration behavior
    - **Property: Token Revocation Consistency**
    - **Validates: Requirements 2.10**
  - [x] 3.3 Integrate token store with JWTService


    - Update `JWTService.verify_token()` to check revocation status
    - Add token revocation endpoint to auth routes
    - _Requirements: 2.10_
  - [x] 3.4 Write integration test for token revocation flow


    - Test complete revocation flow with Redis
    - _Requirements: 2.10_


- [x] 4. Checkpoint - Verify token revocation implementation


  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Add missing property tests for uncovered acceptance criteria



  - [x] 5.1 Write property test for password hashing round-trip

    - Test that hashing and verifying returns true for any password
    - **Property: Password Hash Round-Trip**
    - **Validates: Requirements 2.8**
  - [x] 5.2 Write property test for API versioning deprecation headers


    - Test that deprecated endpoints include Sunset and Deprecation headers
    - **Property: Deprecation Headers Presence**
    - **Validates: Requirements 6.4**
  - [x] 5.3 Write property test for request ID propagation


    - Test that response includes same request ID from request
    - **Property: Request ID Invariant**
    - **Validates: Requirements 4.3**
  - [x] 5.4 Write property test for structured logging JSON format


    - Test that all log entries are valid JSON with required fields
    - **Property: Log Entry JSON Validity**
    - **Validates: Requirements 4.1**





- [x] 6. Update documentation with review findings
  - [x] 6.1 Update architecture.md with conformance status


    - Add conformance score and gap analysis
    - Update diagrams if needed



    - _Requirements: 6.2_
  - [x] 6.2 Create ADR for token revocation decision
    - Document Redis integration decision
    - Include alternatives considered
    - Created `docs/adr/ADR-004-token-revocation.md`
    - _Requirements: 6.1_

- [x] 7. Final Checkpoint - Ensure all tests pass
  - All property-based tests and integration tests implemented
  - Test coverage includes JWT, RBAC, token revocation, security headers, error handling
  - _Status: Complete_
