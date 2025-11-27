# Implementation Plan

- [x] 1. Set up authentication infrastructure
  - [x] 1.1 Create JWT service with token generation and verification



    - Create `src/my_api/core/auth/jwt.py` with JWTService class
    - Implement `create_access_token`, `create_refresh_token`, `verify_token` methods
    - Add TokenPair and TokenPayload dataclasses
    - Use python-jose for JWT operations
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Write property test for token pair generation



    - **Property 1: Token pair generation returns valid structure**
    - **Validates: Requirements 1.1**


  - [x] 1.3 Write property test for token payload round-trip



    - **Property 6: Token payload serialization round-trip**
    - **Validates: Requirements 1.6**

  - [x] 1.4 Implement refresh token storage with Redis



    - Create `src/my_api/infrastructure/auth/token_store.py`
    - Implement RefreshTokenStore with store, revoke, is_valid methods
    - Use Redis for token storage with TTL
    - _Requirements: 1.4, 1.5_


  - [x] 1.5 Write property test for refresh token round-trip


    - **Property 4: Refresh token round-trip**
    - **Validates: Requirements 1.4**


  - [x] 1.6 Write property test for logout invalidation
    - **Property 5: Logout invalidates refresh token**
    - **Validates: Requirements 1.5**




  - [x] 1.7 Write property test for expired token rejection


    - **Property 3: Expired tokens are rejected**
    - **Validates: Requirements 1.3**

- [x] 2. Checkpoint - Ensure all tests pass



  - Ensure all tests pass, ask the user if questions arise.



- [x] 3. Implement RBAC system
  - [x] 3.1 Create RBAC service with permission checking
    - `src/my_api/core/auth/rbac.py` implemented
    - Permission enum with READ, WRITE, DELETE, ADMIN, MANAGE_USERS, MANAGE_ROLES, VIEW_AUDIT, EXPORT_DATA
    - Role dataclass with permissions frozenset
    - RBACService with check_permission, get_user_permissions, check_any_permission, check_all_permissions
    - require_permission decorator implemented
    - Predefined roles: ROLE_ADMIN, ROLE_USER, ROLE_VIEWER, ROLE_MODERATOR
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.2 Write property test for insufficient permissions


    - **Property 7: Insufficient permissions return 403**
    - **Validates: Requirements 2.1**


  - [x] 3.3 Write property test for role permission combination
    - **Property 8: Multiple roles combine permissions**
    - **Validates: Requirements 2.3**

  - [x] 3.4 Create database models for roles and user_roles
    - `src/my_api/domain/entities/role.py` implemented
    - RoleDB and UserRoleDB SQLModel entities
    - RoleCreate, RoleUpdate, RoleResponse DTOs
    - Alembic migration `20241127_000001_002_add_roles_tables.py` created
    - _Requirements: 2.3_




- [x] 4. Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Enhance security headers
  - [x] 5.1 Update SecurityHeadersMiddleware with default CSP and Permissions-Policy
    - SecurityHeadersMiddleware already supports CSP and Permissions-Policy via constructor params
    - Located at `src/my_api/adapters/api/middleware/security_headers.py`
    - Supports `content_security_policy` and `permissions_policy` parameters
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 5.2 Configure default CSP and Permissions-Policy in main.py
    - `src/my_api/main.py` passes CSP and Permissions-Policy from settings
    - `src/my_api/core/config.py` has SecuritySettings with csp and permissions_policy fields
    - Default CSP: "default-src 'self'", Default Permissions-Policy: "geolocation=(), microphone=(), camera=()"
    - Environment variable support via SECURITY__CSP and SECURITY__PERMISSIONS_POLICY
    - _Requirements: 3.1, 3.2, 3.4_



  - [x] 5.3 Write property test for CSP header presence

    - **Property 9: CSP header presence**
    - **Validates: Requirements 3.1**


  - [x] 5.4 Write property test for Permissions-Policy header
    - **Property 10: Permissions-Policy header presence**
    - **Validates: Requirements 3.2**

  - [x] 5.5 Write property test for security header config round-trip
    - **Property 11: Security header config round-trip**
    - **Validates: Requirements 3.5**

- [x] 6. Implement audit logging
  - [x] 6.1 Create audit logger service
    - `src/my_api/infrastructure/audit/logger.py` implemented
    - AuditEntry and AuditFilters dataclasses defined
    - AuditLogger abstract class with log and query methods
    - InMemoryAuditLogger implementation for dev/testing
    - AuditAction and AuditResult enums defined
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 6.2 Create audit log database model and migration
    - `src/my_api/domain/entities/audit_log.py` implemented
    - AuditLogDB SQLModel entity with all required fields
    - Alembic migration `20241127_000002_003_add_audit_logs_table.py` created
    - Indexes for user_id, action, timestamp, resource_type
    - _Requirements: 4.4_

  - [x] 6.3 Write property test for audit log creation

    - **Property 12: Audit log creation for auth actions**
    - **Validates: Requirements 4.1**


  - [x] 6.4 Write property test for audit log filtering
    - **Property 13: Audit log filtering**
    - **Validates: Requirements 4.3**

  - [x] 6.5 Write property test for audit log serialization round-trip
    - **Property 15: Audit log serialization round-trip**
    - **Validates: Requirements 4.5**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement API versioning
  - [x] 8.1 Create versioning infrastructure
    - `src/my_api/adapters/api/versioning.py` implemented
    - APIVersion enum (V1, V2) and VersionConfig dataclass defined
    - VersionedRouter class with prefix and config support
    - DeprecationHeaderMiddleware for deprecated version headers
    - create_versioned_app_routers helper function
    - _Requirements: 5.1, 5.2, 5.5_

  - [x] 8.2 Refactor existing routes to use versioning
    - `src/my_api/main.py` uses VersionedRouter for v1
    - Items routes at /api/v1/items namespace
    - OpenAPI documentation updated for versioning
    - _Requirements: 5.1, 5.4_

  - [x] 8.3 Write property test for version routing

    - **Property 16: API version routing**
    - **Validates: Requirements 5.1, 5.5**


  - [x] 8.4 Write property test for deprecated version headers
    - **Property 17: Deprecated version headers**
    - **Validates: Requirements 5.2**

- [x] 9. Enhance input sanitization
  - [x] 9.1 Basic sanitization utilities exist
    - `src/my_api/shared/utils/sanitization.py` has sanitize_string, sanitize_sql_identifier, sanitize_path, sanitize_dict, strip_dangerous_chars
    - _Requirements: 7.1, 7.2 (partial)_

  - [x] 9.2 Extend sanitization with InputSanitizer class
    - SanitizationType enum implemented in `src/my_api/shared/utils/sanitization.py`
    - InputSanitizer class implemented with sanitize_html, sanitize_sql, sanitize_shell methods
    - Logging for sanitization modifications implemented
    - _Requirements: 7.1, 7.2, 7.4_

  - [x] 9.3 Write property test for valid character preservation

    - **Property 18: Input sanitization preserves valid characters**
    - **Validates: Requirements 7.2**


  - [x] 9.4 Write property test for sanitization round-trip
    - **Property 19: Sanitization round-trip for valid inputs**
    - **Validates: Requirements 7.5**

  - [x] 9.5 Write property test for dangerous character removal
    - **Property 20: Dangerous character removal**
    - **Validates: Requirements 7.1**

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement password policy
  - [x] 11.1 Create password policy validator
    - `src/my_api/core/auth/password_policy.py` implemented
    - PasswordPolicy and PasswordValidationResult dataclasses defined
    - PasswordValidator with validate method implemented
    - Common passwords list checking implemented
    - Integrated with Argon2id hashing from `src/my_api/shared/utils/password.py`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 11.2 Write property test for minimum length enforcement
    - **Property 26: Password minimum length enforcement**
    - **Validates: Requirements 10.1**

  - [x] 11.3 Write property test for complexity requirements
    - **Property 27: Password complexity requirements**
    - **Validates: Requirements 10.2**

  - [x] 11.4 Write property test for validation feedback specificity
    - **Property 28: Password validation feedback specificity**
    - **Validates: Requirements 10.3**

  - [x] 11.5 Write property test for common password rejection
    - **Property 29: Common password rejection**
    - **Validates: Requirements 10.5**

- [x] 12. Enhance health checks
  - [x] 12.1 Update health check endpoints
    - Health checks already implemented in `src/my_api/adapters/api/routes/health.py`
    - Database connectivity check exists with timeout support
    - Redis connectivity check exists (returns degraded if unavailable)
    - Returns detailed component status on failure with 503
    - Liveness probe at `/health/live`, readiness at `/health/ready`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 12.2 Health check property tests exist
    - Tests in `tests/properties/test_health_properties.py`
    - Covers healthy/unhealthy database, Redis degraded, timeout handling
    - Tests overall status determination logic
    - _Requirements: 8.3, 8.5_

- [x] 13. Implement request/response logging
  - [x] 13.1 Create logging middleware
    - `src/my_api/adapters/api/middleware/request_logger.py` implemented
    - Logs method, path, headers, sanitized body
    - Logs response status, duration, size
    - Sensitive data masking implemented
    - Request_id included in all entries
    - _Requirements: 9.1, 9.2, 9.3, 9.5_

  - [x] 13.2 Write property test for request logging completeness
    - **Property 23: Request logging completeness**
    - **Validates: Requirements 9.1**

  - [x] 13.3 Write property test for sensitive data masking
    - **Property 24: Sensitive data masking**
    - **Validates: Requirements 9.3**

  - [x] 13.4 Write property test for request ID correlation
    - **Property 25: Request ID correlation**
    - **Validates: Requirements 9.5**

- [x] 14. Create ADR documentation
  - [x] 14.1 Create ADR template and initial ADRs
    - `docs/adr/` directory created
    - ADR-000-template.md created
    - ADR-001-jwt-authentication.md written
    - ADR-002-rbac-implementation.md written
    - ADR-003-api-versioning.md written
    - _Requirements: 6.1, 6.2_

- [x] 15. Wire authentication into main application
  - [x] 15.1 Integrate auth components into FastAPI app
    - `src/my_api/adapters/api/routes/auth.py` created
    - Auth routes (login, logout, refresh, me) implemented
    - `src/my_api/main.py` updated with auth routes
    - DI container wired with auth services
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 2.1_

  - [x] 15.2 Write property test for valid token authentication
    - **Property 2: Valid token authentication provides user context**
    - **Validates: Requirements 1.2**

- [x] 16. Final Checkpoint - Ensure all tests pass

  - Ensure all tests pass, ask the user if questions arise.
