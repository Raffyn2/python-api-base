# ADR-022: Code Review Improvements December 2025

## Status
Accepted

## Context
Code review identified several improvements needed:
1. Thread-safety issue in DI container singleton initialization
2. CORS wildcard allowed in staging environment
3. Unsafe dict access in users router
4. Missing contract tests

## Decision

### 1. Thread-Safe Container Initialization
Added double-check locking pattern to `_get_container()` in `interface/dependencies.py`:
- Prevents race conditions during container creation
- Uses `threading.Lock()` for synchronization

### 2. CORS Security Enhancement
Extended CORS validation in `core/config/security.py`:
- Block wildcard `*` in both production AND staging
- Added `restricted_envs = {"production", "staging", "prod", "stg"}`
- Improved warning message with current environment

### 3. Safe Dict Access
Updated `interface/v1/users_router.py`:
- Changed `u["field"]` to `u.get("field", default)`
- Prevents KeyError on missing optional fields
- Added sensible defaults for required fields

### 4. Contract Tests
Created `tests/contract/` with:
- `test_users_contract.py`: User API schema validation
- `test_auth_contract.py`: OAuth2/RFC 7807 compliance
- `test_health_contract.py`: Health endpoint contracts

## Consequences

### Positive
- Thread-safe initialization prevents race conditions
- Stricter CORS improves security posture
- Safe dict access prevents runtime errors
- Contract tests ensure API stability for consumers

### Negative
- Slight overhead from lock acquisition (negligible)
- Stricter CORS may require config changes for staging

### Neutral
- Contract tests add maintenance burden but provide value

## Alternatives Rejected
1. Module-level container initialization: Would fail if settings not ready
2. Per-request container: Too expensive, breaks singleton semantics
3. Runtime CORS validation: Too late, should fail at startup

## References
- Python threading: https://docs.python.org/3/library/threading.html
- RFC 7807 Problem Details: https://tools.ietf.org/html/rfc7807
- OAuth2 Token Response: https://tools.ietf.org/html/rfc6749#section-5.1
