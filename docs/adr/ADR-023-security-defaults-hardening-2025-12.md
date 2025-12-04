# ADR-023: Security Defaults Hardening

## Status
Accepted

## Date
2025-12-04

## Context
Code review identified security vulnerabilities in default configurations:

1. `SecuritySettings.algorithm` defaulted to `HS256` (symmetric)
2. `CORSPolicy.allow_origins` defaulted to `["*"]` (wildcard)
3. Circuit breaker returned raw JSON instead of RFC 7807
4. Router exception handlers caught bare `Exception` without re-raising `HTTPException`

These defaults could lead to security misconfigurations in production deployments.

## Decision

### 1. JWT Algorithm Default: HS256 → RS256
- Asymmetric algorithms (RS256/ES256) are security best practice
- Private key stays on server, public key can be distributed
- Prevents algorithm confusion attacks
- Location: `src/core/config/security.py`

### 2. CORS Origins Default: ["*"] → []
- Empty list forces explicit origin configuration
- Wildcard already blocked in production via validator
- Defense in depth approach
- Location: `src/interface/middleware/security/cors_manager.py`

### 3. Circuit Breaker RFC 7807 Compliance
- Error responses now use `ProblemDetail.service_unavailable()`
- Includes `Retry-After` header via problem detail
- Consistent error format across API
- Location: `src/interface/middleware/production.py`

### 4. Exception Handler Specificity
- Added explicit `except HTTPException: raise` before generic catch
- Preserves FastAPI exception handling chain
- Prevents swallowing framework exceptions
- Location: `src/interface/router.py`

## Consequences

### Positive
- Secure by default configuration
- OWASP compliance improved
- Consistent RFC 7807 error responses
- Better exception stack preservation

### Negative
- Existing deployments using HS256 need migration
- CORS must be explicitly configured (no more implicit wildcard)

### Neutral
- No performance impact
- Backward compatible with explicit configuration

## Alternatives Rejected

1. Keep HS256 default with warning: Rejected - security over convenience
2. Keep wildcard CORS with production block only: Rejected - defense in depth
3. Custom error format for circuit breaker: Rejected - RFC 7807 standardization

## References
- OWASP JWT Security Cheat Sheet
- RFC 7807 Problem Details for HTTP APIs
- ADR-001-jwt-authentication.md
- ADR-019-cors-security-policy.md
