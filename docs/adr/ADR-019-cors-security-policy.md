# ADR-019: CORS Security Policy

## Status
Accepted

## Date
2025-12-04

## Context

The API uses CORS (Cross-Origin Resource Sharing) to control which origins can access resources. The current implementation in `CORSManager` defaults to `allow_origins=["*"]` (wildcard), which is permissive and may pose security risks in production environments.

### Current Implementation
- Location: `src/interface/middleware/security/cors_manager.py`
- Default: `CORSPolicy(allow_origins=["*"])`
- Warning: `SecuritySettings.warn_wildcard_cors()` logs warning in production

### Security Concerns
1. Wildcard CORS allows any origin to make requests
2. Combined with `allow_credentials=True`, this creates CSRF vulnerabilities
3. No explicit documentation of acceptable use cases

## Decision

### 1. Environment-Based CORS Policy

| Environment | Policy | Rationale |
|-------------|--------|-----------|
| Development | Wildcard (`*`) allowed | Developer convenience |
| Staging | Explicit origins only | Mirror production |
| Production | Explicit origins only | Security requirement |

### 2. Configuration Guidelines

```python
# Production - REQUIRED: Explicit origins
CORS_ORIGINS=["https://app.example.com", "https://admin.example.com"]

# Development - ALLOWED: Wildcard
CORS_ORIGINS=["*"]
```

### 3. Credentials Rule
- `allow_credentials=True` MUST NOT be combined with wildcard origins
- Enforced in `CORSPolicy.to_headers()` method

### 4. Monitoring
- Log all CORS rejections with origin details
- Alert on unexpected origin patterns in production

## Consequences

### Positive
- Clear security boundaries per environment
- Documented policy for team reference
- Existing warning mechanism validates compliance

### Negative
- Requires explicit origin configuration for production deployments
- May require updates when adding new frontend domains

### Neutral
- No code changes required (policy documentation only)
- Existing `warn_wildcard_cors` validator remains active

## Alternatives Rejected

1. **Remove wildcard support entirely**: Rejected - breaks development workflow
2. **Runtime origin validation only**: Rejected - insufficient for compliance audits
3. **Automatic origin detection**: Rejected - security risk, unpredictable behavior

## Compliance

- OWASP: Access-Control-Allow-Origin validation
- CWE-942: Overly Permissive Cross-domain Whitelist

## References

- [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP CORS](https://owasp.org/www-community/attacks/CORS_OriginHeaderScrutiny)
