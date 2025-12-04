# Design Document: API Best Practices Review 2025

## Overview

Este documento de design detalha a arquitetura e implementação das melhores práticas para o Python API Base em 2024/2025. O objetivo é garantir que a API siga padrões enterprise-grade em segurança, performance, observabilidade e resiliência.

A revisão abrange 28 requisitos organizados em 8 categorias principais:
1. Framework e Arquitetura (FastAPI, Clean Architecture, DDD, CQRS)
2. Segurança (JWT RS256, RBAC, Zero Trust)
3. Observabilidade (OpenTelemetry, Prometheus, structlog)
4. Resiliência (Circuit Breaker, Retry, Bulkhead)
5. Banco de Dados (SQLAlchemy 2.0, SQLModel, Partitioning)
6. Cache e Performance (Redis TTL Jitter, Pydantic V2)
7. APIs Avançadas (GraphQL, Idempotency, Health Checks)
8. Integração e Testes (ItemExample, PedidoExample, Docker)

## Architecture

### Diagrama de Camadas (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            INTERFACE LAYER                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ REST API    │  │ GraphQL     │  │ Health      │  │ Middleware          │ │
│  │ (FastAPI)   │  │ (Strawberry)│  │ Endpoints   │  │ (Security, Logging) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                           APPLICATION LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Commands    │  │ Queries     │  │ DTOs        │  │ Services            │ │
│  │ (CQRS)      │  │ (CQRS)      │  │ (Pydantic)  │  │ (Feature Flags)     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                            DOMAIN LAYER                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Entities    │  │ Value       │  │ Specifica-  │  │ Domain Events       │ │
│  │ (Item,      │  │ Objects     │  │ tions       │  │ (Created, Updated)  │ │
│  │  Pedido)    │  │ (Money)     │  │ (Composable)│  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                         INFRASTRUCTURE LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Repositories│  │ Cache       │  │ Auth        │  │ Resilience          │ │
│  │ (SQLAlchemy)│  │ (Redis)     │  │ (JWT RS256) │  │ (Circuit Breaker)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                             CORE LAYER                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Config      │  │ DI          │  │ Protocols   │  │ Types               │ │
│  │ (Settings)  │  │ (Container) │  │ (Interfaces)│  │ (EntityId, Result)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Request

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Client  │───▶│  Middleware  │───▶│   Router     │───▶│  Use Case    │
└──────────┘    │  - Auth      │    │  - Validate  │    │  - Command   │
                │  - RateLimit │    │  - Serialize │    │  - Query     │
                │  - Logging   │    │              │    │              │
                └──────────────┘    └──────────────┘    └──────────────┘
                                                               │
                       ┌───────────────────────────────────────┘
                       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Domain     │◀──▶│  Repository  │◀──▶│    Cache     │◀──▶│   Database   │
│   Entity     │    │  (Generic)   │    │   (Redis)    │    │  (PostgreSQL)│
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐
│ Domain Event │───▶│  Event Bus   │───▶ Handlers (Audit, Notifications)
└──────────────┘    └──────────────┘
```

## Components and Interfaces

### 1. JWT Authentication (RS256)

```python
# Interface
class IJWTService(Protocol):
    def create_access_token(self, user_id: str, roles: list[str]) -> str: ...
    def create_refresh_token(self, user_id: str) -> str: ...
    def verify_token(self, token: str) -> TokenPayload: ...
    def get_jwks(self) -> dict: ...

# Implementation
class JWTServiceRS256:
    def __init__(self, private_key: RSAPrivateKey, public_key: RSAPublicKey):
        self._private_key = private_key
        self._public_key = public_key
        self._kid = generate_key_id(public_key)
    
    def create_access_token(self, user_id: str, roles: list[str]) -> str:
        payload = {
            "sub": user_id,
            "roles": roles,
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "jti": str(uuid4()),
        }
        return jwt.encode(payload, self._private_key, algorithm="RS256", 
                         headers={"kid": self._kid})
    
    def get_jwks(self) -> dict:
        """Expose public key via JWKS endpoint."""
        return {
            "keys": [{
                "kty": "RSA",
                "kid": self._kid,
                "use": "sig",
                "alg": "RS256",
                "n": base64url_encode(self._public_key.public_numbers().n),
                "e": base64url_encode(self._public_key.public_numbers().e),
            }]
        }
```

### 2. Redis Cache with TTL Jitter

```python
class RedisCacheWithJitter:
    def __init__(self, redis: Redis, jitter_percent: float = 0.1):
        self._redis = redis
        self._jitter_percent = jitter_percent
    
    def _apply_jitter(self, ttl: int) -> int:
        """Add random jitter to TTL to prevent thundering herd."""
        jitter = int(ttl * self._jitter_percent * random.random())
        return ttl + jitter
    
    async def set(self, key: str, value: Any, ttl: int) -> None:
        jittered_ttl = self._apply_jitter(ttl)
        await self._redis.setex(key, jittered_ttl, serialize(value))
    
    async def get_or_compute(
        self, 
        key: str, 
        compute: Callable[[], Awaitable[T]], 
        ttl: int,
        lock_timeout: int = 5
    ) -> T:
        """Get from cache or compute with distributed lock."""
        cached = await self._redis.get(key)
        if cached:
            return deserialize(cached)
        
        # Distributed lock to prevent stampede
        lock_key = f"lock:{key}"
        if await self._redis.set(lock_key, "1", nx=True, ex=lock_timeout):
            try:
                value = await compute()
                await self.set(key, value, ttl)
                return value
            finally:
                await self._redis.delete(lock_key)
        else:
            # Wait and retry
            await asyncio.sleep(0.1)
            return await self.get_or_compute(key, compute, ttl, lock_timeout)
```

### 3. Pydantic V2 Performance Patterns

```python
from pydantic import BaseModel, TypeAdapter, computed_field, FailFast
from functools import lru_cache
from typing import Annotated

# TypeAdapter instantiated once (not per request)
ItemListAdapter = TypeAdapter(list[ItemDTO])

class ItemDTO(BaseModel):
    id: str
    name: str
    price: Decimal
    category: str
    
    @computed_field
    @property
    @lru_cache(maxsize=1)
    def display_price(self) -> str:
        return f"R$ {self.price:.2f}"

# Use model_validate_json for direct JSON parsing
async def create_item(request: Request) -> ItemDTO:
    body = await request.body()
    return ItemDTO.model_validate_json(body)

# Use FailFast for early validation failure
FastItemList = Annotated[list[ItemDTO], FailFast()]

# Use TypedDict for simple nested structures
class ItemMetadata(TypedDict):
    created_at: str
    updated_at: str
    version: int
```

### 4. Idempotency Handler

```python
class IdempotencyHandler:
    def __init__(self, redis: Redis, ttl_hours: int = 24):
        self._redis = redis
        self._ttl = ttl_hours * 3600
    
    async def execute_idempotent(
        self,
        idempotency_key: str,
        request_hash: str,
        operation: Callable[[], Awaitable[Response]]
    ) -> Response:
        cache_key = f"idempotency:{idempotency_key}"
        
        # Check if already processed
        cached = await self._redis.get(cache_key)
        if cached:
            stored = json.loads(cached)
            if stored["request_hash"] != request_hash:
                raise HTTPException(422, "Idempotency key reused with different request")
            return Response(
                content=stored["response_body"],
                status_code=stored["status_code"],
                headers={"X-Idempotent-Replayed": "true"}
            )
        
        # Execute operation
        response = await operation()
        
        # Store result
        await self._redis.setex(
            cache_key,
            self._ttl,
            json.dumps({
                "request_hash": request_hash,
                "response_body": response.body.decode(),
                "status_code": response.status_code
            })
        )
        
        return response
```

### 5. Health Check System

```python
class HealthCheckService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self._db = db
        self._redis = redis
        self._ready = False
    
    async def liveness(self) -> dict:
        """Simple liveness check - process is running."""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    
    async def readiness(self) -> dict:
        """Readiness check - all dependencies available."""
        checks = {
            "database": await self._check_database(),
            "redis": await self._check_redis(),
        }
        all_healthy = all(c["status"] == "healthy" for c in checks.values())
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def startup(self) -> None:
        """Startup probe - wait for dependencies."""
        max_retries = 30
        for i in range(max_retries):
            try:
                await self._db.execute(text("SELECT 1"))
                await self._redis.ping()
                self._ready = True
                return
            except Exception:
                await asyncio.sleep(1)
        raise RuntimeError("Failed to connect to dependencies")
    
    async def _check_database(self) -> dict:
        try:
            await self._db.execute(text("SELECT 1"))
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_redis(self) -> dict:
        try:
            await self._redis.ping()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```



## Data Models

### JWT Token Payload

```python
class TokenPayload(BaseModel):
    sub: str  # user_id
    roles: list[str]
    exp: datetime
    iat: datetime
    jti: str  # unique token ID
    aud: str | None = None
    iss: str | None = None

class JWKSResponse(BaseModel):
    keys: list[JWK]

class JWK(BaseModel):
    kty: Literal["RSA"]
    kid: str
    use: Literal["sig"]
    alg: Literal["RS256"]
    n: str  # modulus
    e: str  # exponent
```

### Cache Entry with Jitter

```python
class CacheEntry(BaseModel):
    key: str
    value: Any
    ttl: int
    jittered_ttl: int
    created_at: datetime
    expires_at: datetime

class CacheStats(BaseModel):
    hits: int
    misses: int
    hit_ratio: float
    avg_ttl: float
```

### Idempotency Record

```python
class IdempotencyRecord(BaseModel):
    idempotency_key: str
    request_hash: str
    response_body: str
    status_code: int
    created_at: datetime
    expires_at: datetime
```

### Health Check Response

```python
class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

class DependencyHealth(BaseModel):
    status: HealthStatus
    latency_ms: float | None = None
    error: str | None = None

class HealthResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime
    checks: dict[str, DependencyHealth] | None = None
    version: str | None = None
```

### ItemExample Entity (Existing)

```python
class ItemExample(BaseEntity):
    id: str
    name: str
    description: str | None
    price: Money
    category: str
    tags: list[str]
    stock_quantity: int
    status: ItemExampleStatus
    tenant_id: str
    created_at: datetime
    updated_at: datetime

class Money(ValueObject):
    amount: Decimal
    currency: str = "BRL"

class ItemExampleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
```

### PedidoExample Entity (Existing)

```python
class PedidoExample(BaseEntity):
    id: str
    customer_id: str
    items: list[PedidoItemExample]
    status: PedidoStatus
    total: Money
    tenant_id: str
    created_at: datetime
    confirmed_at: datetime | None

class PedidoItemExample(ValueObject):
    item_id: str
    quantity: int
    unit_price: Money

class PedidoStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis, the following correctness properties have been identified:

### Property 1: JWT RS256 Algorithm Enforcement
*For any* JWT token generated by the system, the token header SHALL contain algorithm "RS256" and a valid "kid" (key ID) field.
**Validates: Requirements 2.1, 20.1**

### Property 2: JWT Round-Trip Consistency
*For any* valid token payload (user_id, roles, expiration), encoding with the private key and decoding with the public key SHALL return an equivalent payload.
**Validates: Requirements 7.2**

### Property 3: JWT Key Rotation Backward Compatibility
*For any* token signed with a previous key (within grace period), validation with the current JWKS SHALL succeed if the old key is still in the key set.
**Validates: Requirements 20.3**

### Property 4: JWT Kid Validation
*For any* token with a "kid" header not present in the JWKS, validation SHALL fail with an appropriate error.
**Validates: Requirements 20.4**

### Property 5: RBAC Permission Composition
*For any* role hierarchy (admin > editor > viewer), a user with a higher role SHALL have all permissions of lower roles.
**Validates: Requirements 7.3**

### Property 6: Repository CRUD Consistency
*For any* entity, creating and then reading by ID SHALL return an equivalent entity; updating and then reading SHALL return the updated entity.
**Validates: Requirements 7.4**

### Property 7: Specification Composition Laws
*For any* two specifications A and B, the following laws SHALL hold:
- Commutativity: A AND B == B AND A, A OR B == B OR A
- Double Negation: NOT(NOT A) == A
- De Morgan: NOT(A AND B) == NOT(A) OR NOT(B)
**Validates: Requirements 7.5**

### Property 8: Pydantic JSON Validation Equivalence
*For any* valid JSON string representing a model, model_validate_json(json_str) SHALL produce an equivalent result to model_validate(json.loads(json_str)).
**Validates: Requirements 19.1**

### Property 9: Cache TTL Jitter Range
*For any* base TTL value, the jittered TTL SHALL be within the range [base_ttl, base_ttl * 1.15] (5-15% jitter).
**Validates: Requirements 22.1**

### Property 10: Cache Stampede Prevention
*For any* cache miss with concurrent requests for the same key, only one computation SHALL be executed (others wait for result).
**Validates: Requirements 22.3**

### Property 11: Idempotency Key Replay
*For any* request with an Idempotency-Key header, sending the same request multiple times SHALL return the same response without re-executing the operation.
**Validates: Requirements 23.1, 23.3**

### Property 12: Idempotency Key Conflict Detection
*For any* Idempotency-Key, using the same key with a different request body SHALL result in a 422 error.
**Validates: Requirements 23.4**

### Property 13: ItemExample CRUD Consistency
*For any* ItemExample entity, creating via POST /api/v1/items and reading via GET /api/v1/items/{id} SHALL return equivalent data.
**Validates: Requirements 26.1, 28.1**

### Property 14: Specification Filtering Correctness
*For any* ItemExample query with specifications (category, price range, availability), all returned items SHALL satisfy the specification criteria.
**Validates: Requirements 26.4, 28.3**

## Error Handling

### Error Response Format (RFC 7807)

```python
class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    # Extensions
    correlation_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Example error responses
VALIDATION_ERROR = ProblemDetail(
    type="https://api.example.com/errors/validation",
    title="Validation Error",
    status=422,
    detail="Request body contains invalid data"
)

IDEMPOTENCY_CONFLICT = ProblemDetail(
    type="https://api.example.com/errors/idempotency-conflict",
    title="Idempotency Key Conflict",
    status=422,
    detail="Idempotency key was already used with a different request body"
)

JWT_INVALID = ProblemDetail(
    type="https://api.example.com/errors/jwt-invalid",
    title="Invalid Token",
    status=401,
    detail="The provided JWT token is invalid or expired"
)
```

### Error Categories

| Category | Status Code | Use Case |
|----------|-------------|----------|
| ValidationError | 422 | Invalid request body, missing fields |
| AuthenticationError | 401 | Invalid/expired JWT, missing token |
| AuthorizationError | 403 | Insufficient permissions (RBAC) |
| NotFoundError | 404 | Resource not found |
| ConflictError | 409 | Resource already exists |
| IdempotencyError | 422 | Idempotency key conflict |
| RateLimitError | 429 | Rate limit exceeded |
| InternalError | 500 | Unexpected server error |

## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific examples and property-based tests for universal properties.

#### Property-Based Testing (Hypothesis)

```python
from hypothesis import given, strategies as st, settings

# Property 1: JWT RS256 Algorithm Enforcement
@given(
    user_id=st.uuids().map(str),
    roles=st.lists(st.sampled_from(["admin", "editor", "viewer"]), min_size=1)
)
@settings(max_examples=100)
def test_jwt_uses_rs256_algorithm(jwt_service, user_id, roles):
    """
    **Feature: api-best-practices-review-2025, Property 1: JWT RS256 Algorithm Enforcement**
    """
    token = jwt_service.create_access_token(user_id, roles)
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "RS256"
    assert "kid" in header

# Property 2: JWT Round-Trip Consistency
@given(
    user_id=st.uuids().map(str),
    roles=st.lists(st.sampled_from(["admin", "editor", "viewer"]), min_size=1)
)
@settings(max_examples=100)
def test_jwt_round_trip(jwt_service, user_id, roles):
    """
    **Feature: api-best-practices-review-2025, Property 2: JWT Round-Trip Consistency**
    """
    token = jwt_service.create_access_token(user_id, roles)
    payload = jwt_service.verify_token(token)
    assert payload.sub == user_id
    assert set(payload.roles) == set(roles)

# Property 7: Specification Composition Laws
@given(
    field=st.sampled_from(["category", "status", "price"]),
    value1=st.text(min_size=1, max_size=10),
    value2=st.text(min_size=1, max_size=10)
)
@settings(max_examples=100)
def test_specification_commutativity(field, value1, value2):
    """
    **Feature: api-best-practices-review-2025, Property 7: Specification Composition Laws**
    """
    spec_a = equals(field, value1)
    spec_b = equals(field, value2)
    
    # AND commutativity
    and_ab = spec_a.and_spec(spec_b)
    and_ba = spec_b.and_spec(spec_a)
    assert and_ab.to_dict() == and_ba.to_dict()
    
    # OR commutativity
    or_ab = spec_a.or_spec(spec_b)
    or_ba = spec_b.or_spec(spec_a)
    assert or_ab.to_dict() == or_ba.to_dict()

# Property 9: Cache TTL Jitter Range
@given(base_ttl=st.integers(min_value=60, max_value=86400))
@settings(max_examples=100)
def test_cache_ttl_jitter_range(cache_service, base_ttl):
    """
    **Feature: api-best-practices-review-2025, Property 9: Cache TTL Jitter Range**
    """
    jittered = cache_service._apply_jitter(base_ttl)
    assert base_ttl <= jittered <= base_ttl * 1.15

# Property 11: Idempotency Key Replay
@given(
    idempotency_key=st.uuids().map(str),
    request_body=st.dictionaries(st.text(min_size=1), st.text())
)
@settings(max_examples=100)
async def test_idempotency_replay(idempotency_handler, idempotency_key, request_body):
    """
    **Feature: api-best-practices-review-2025, Property 11: Idempotency Key Replay**
    """
    request_hash = hash_request(request_body)
    
    # First request
    response1 = await idempotency_handler.execute_idempotent(
        idempotency_key, request_hash, lambda: create_response(request_body)
    )
    
    # Second request (replay)
    response2 = await idempotency_handler.execute_idempotent(
        idempotency_key, request_hash, lambda: create_response(request_body)
    )
    
    assert response1.body == response2.body
    assert response1.status_code == response2.status_code
```

#### Unit Tests

```python
# Example: JWKS endpoint returns valid format
def test_jwks_endpoint_returns_valid_format(jwt_service):
    """Test JWKS endpoint returns valid JWK format."""
    jwks = jwt_service.get_jwks()
    assert "keys" in jwks
    assert len(jwks["keys"]) > 0
    
    key = jwks["keys"][0]
    assert key["kty"] == "RSA"
    assert key["alg"] == "RS256"
    assert key["use"] == "sig"
    assert "kid" in key
    assert "n" in key
    assert "e" in key

# Example: Liveness endpoint returns 200
async def test_liveness_returns_200(health_service):
    """Test liveness check returns healthy status."""
    response = await health_service.liveness()
    assert response["status"] == "healthy"
    assert "timestamp" in response

# Example: Readiness fails when database unavailable
async def test_readiness_fails_without_database(health_service_no_db):
    """Test readiness check fails when database is unavailable."""
    response = await health_service_no_db.readiness()
    assert response["status"] == "unhealthy"
    assert response["checks"]["database"]["status"] == "unhealthy"
```

### Test Coverage Requirements

| Category | Minimum Coverage | Focus Areas |
|----------|-----------------|-------------|
| Domain Layer | 90% | Entities, Value Objects, Specifications |
| Application Layer | 85% | Use Cases, Commands, Queries |
| Infrastructure Layer | 80% | Repositories, Cache, Auth |
| Interface Layer | 75% | Routes, Middleware, Error Handlers |

### Integration Tests with Docker

```python
@pytest.fixture(scope="session")
def docker_compose():
    """Start Docker Compose for integration tests."""
    subprocess.run(
        ["docker", "compose", "-f", "deployments/docker/docker-compose.base.yml", "up", "-d"],
        check=True
    )
    yield
    subprocess.run(
        ["docker", "compose", "-f", "deployments/docker/docker-compose.base.yml", "down"],
        check=True
    )

@pytest.mark.integration
async def test_item_example_crud_via_api(docker_compose, api_client):
    """Test ItemExample CRUD operations via REST API."""
    # Create
    item_data = {"name": "Test Item", "price": 99.99, "category": "test"}
    response = await api_client.post("/api/v1/items", json=item_data)
    assert response.status_code == 201
    item_id = response.json()["id"]
    
    # Read
    response = await api_client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"
    
    # Update
    response = await api_client.patch(f"/api/v1/items/{item_id}", json={"price": 149.99})
    assert response.status_code == 200
    
    # Delete
    response = await api_client.delete(f"/api/v1/items/{item_id}")
    assert response.status_code == 204
```

