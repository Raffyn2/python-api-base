# ADR-014: API Best Practices 2025 Implementation

## Status

**Accepted**

## Context

As part of the 2025 API architecture review, we identified several areas requiring enhancement to align with current best practices:

1. **JWT Security**: Move from HS256 (symmetric) to RS256 (asymmetric)
2. **Cache Reliability**: Prevent thundering herd and cache stampede
3. **API Reliability**: Implement idempotency for mutation operations
4. **Health Checks**: Kubernetes-compatible probes
5. **Graceful Shutdown**: Handle SIGTERM properly

## Decision

### 1. JWT RS256 with JWKS

**Implementation:** `src/infrastructure/auth/jwt/jwks.py`

- Use RS256 algorithm with auto-generated `kid` header
- Expose JWKS endpoint at `/.well-known/jwks.json`
- Support key rotation with configurable grace period

```python
# Token header now includes kid
{
    "alg": "RS256",
    "typ": "JWT",
    "kid": "abc123..."  # Auto-generated from public key
}
```

**Endpoint:** `GET /.well-known/jwks.json`

### 2. Redis Cache with TTL Jitter

**Implementation:** `src/infrastructure/cache/providers/redis_jitter.py`

- Apply 5-15% random jitter to TTL values
- Distributed locking for cache stampede prevention
- Probabilistic early recomputation (stale-while-revalidate)

```python
cache = RedisCacheWithJitter[dict](
    config=JitterConfig(
        min_jitter_percent=0.05,
        max_jitter_percent=0.15,
    )
)
```

### 3. API Idempotency

**Implementation:** `src/infrastructure/idempotency/`

- `Idempotency-Key` header for POST/PATCH/PUT operations
- Redis storage with 24-hour TTL
- Request body hashing for conflict detection
- 422 response on key reuse with different body

```python
# Request
POST /api/v1/orders
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

# Response (replay)
HTTP/1.1 200 OK
X-Idempotent-Replayed: true
```

### 4. Health Check Endpoints

**Implementation:** `src/interface/v1/health_router.py`

| Endpoint | Purpose | Kubernetes Probe |
|----------|---------|-----------------|
| `/health/live` | Process alive | Liveness |
| `/health/ready` | Dependencies ready | Readiness |
| `/health/startup` | Initialization complete | Startup |

### 5. Graceful Shutdown

**Implementation:** `src/infrastructure/lifecycle/shutdown.py`

- SIGTERM/SIGINT signal handlers
- In-flight request tracking
- Configurable drain timeout (default: 30s)
- Shutdown hooks for cleanup

## Consequences

### Positive

- **Security**: RS256 prevents key compromise from exposing all tokens
- **Reliability**: Jitter prevents synchronized cache expiration
- **Idempotency**: Safe retry for network failures
- **Operations**: Proper Kubernetes integration

### Negative

- **Complexity**: More moving parts to manage
- **Dependencies**: Redis required for idempotency
- **Performance**: Slight overhead from kid lookup

### Neutral

- **Migration**: Existing HS256 tokens need rotation period

## Property Tests

All implementations verified with Hypothesis property-based tests:

| Module | Tests | File |
|--------|-------|------|
| JWT RS256 | 12 | `test_api_best_practices_2025_jwt_properties.py` |
| Cache Jitter | 11 | `test_api_best_practices_2025_cache_properties.py` |
| Idempotency | 11 | `test_api_best_practices_2025_idempotency_properties.py` |
| Health | 14 | `test_api_best_practices_2025_health_properties.py` |
| Specification | 19 | `test_api_best_practices_2025_specification_properties.py` |
| Repository | 11 | `test_api_best_practices_2025_repository_properties.py` |

**Total: 78 property tests**

## References

- [RFC 7517 - JSON Web Key (JWK)](https://tools.ietf.org/html/rfc7517)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Stripe Idempotency](https://stripe.com/docs/api/idempotent_requests)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Revision History

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-03 | 1.0 | Initial implementation |
