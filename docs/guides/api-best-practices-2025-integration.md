# API Best Practices 2025 - Guia de Integração

Este documento descreve os módulos implementados e sua integração com ItemExample e PedidoExample.

## Módulos Integrados

| Módulo | Local | Status | Usado Por |
|--------|-------|--------|-----------|
| JWKS | `infrastructure/auth/jwt/jwks.py` | ✅ Integrado | `main.py` startup |
| RedisCacheWithJitter | `infrastructure/cache/providers/redis_jitter.py` | ✅ Integrado | `ItemExampleUseCase` |
| Pydantic V2 Utils | `core/shared/validation/pydantic_v2.py` | ✅ Integrado | `examples/router.py` |
| IdempotencyMiddleware | `infrastructure/idempotency/middleware.py` | ✅ Integrado | `POST /api/v1/examples/*` |
| Health Startup | `interface/v1/health_router.py` | ✅ Integrado | `/health/startup` |

## 1. JWKS Endpoint

**Já integrado ao main.py**

Acesse em:
- `GET /.well-known/jwks.json` - Retorna chaves públicas
- `GET /.well-known/openid-configuration` - Configuração OIDC

```bash
# Testar
curl http://localhost:8000/.well-known/jwks.json
```

## 2. RedisCacheWithJitter

### Como usar com ItemExample:

```python
from infrastructure.cache.providers import RedisCacheWithJitter, JitterConfig
from domain.examples.item.entity import ItemExample

# Criar cache com jitter
cache = RedisCacheWithJitter[ItemExample](
    redis_client=redis,  # AsyncRedis client
    config=JitterConfig(
        min_jitter_percent=0.05,  # 5% mínimo
        max_jitter_percent=0.15,  # 15% máximo
    ),
)

# Usar no UseCase
async def get_item_cached(item_id: str) -> ItemExample:
    return await cache.get_or_compute(
        key=f"item:{item_id}",
        compute_fn=lambda: repository.get_by_id(item_id),
        ttl=300,  # 5 min com jitter automático
    )
```

## 3. Pydantic V2 Performance

### Usar TypeAdapterCache para validação rápida:

```python
from core.shared.validation import TypeAdapterCache, validate_json_fast

# Cache de adapter (instancie uma vez)
item_adapter = TypeAdapterCache(ItemExampleResponse)

# Validação rápida de JSON
item = item_adapter.validate_json(b'{"id": "123", "name": "Test"}')

# Serialização rápida
json_bytes = item_adapter.dump_json(item)
```

### Usar computed_field em DTOs:

```python
from pydantic import BaseModel, computed_field

class OrderDTO(BaseModel):
    items: list[ItemDTO]
    
    @computed_field
    @property
    def total_value(self) -> float:
        return sum(item.price * item.quantity for item in self.items)
```

## 4. IdempotencyMiddleware (HTTP)

### Adicionar ao app:

```python
# Em main.py
from infrastructure.idempotency import IdempotencyMiddleware, IdempotencyHandler

# Após Redis estar disponível
if app.state.redis:
    idempotency_handler = IdempotencyHandler(
        redis_url=settings.observability.redis_url
    )
    app.add_middleware(
        IdempotencyMiddleware,
        handler=idempotency_handler,
        required_endpoints={"/api/v1/examples/items"},
        methods={"POST", "PUT"},
    )
```

### Usar no cliente:

```bash
# Request com idempotency key
curl -X POST http://localhost:8000/api/v1/examples/items \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-request-id-123" \
  -d '{"name": "Test", "price": 10.0}'

# Replay (retorna resposta cacheada)
curl -X POST http://localhost:8000/api/v1/examples/items \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-request-id-123" \
  -d '{"name": "Test", "price": 10.0}'
```

## 5. Health Endpoints

**Já integrados:**

```bash
# Liveness (sempre 200 se processo vivo)
curl http://localhost:8000/health/live

# Readiness (verifica dependências)
curl http://localhost:8000/health/ready

# Startup (indica inicialização completa)
curl http://localhost:8000/health/startup
```

## Testando via Docker

```bash
# Subir ambiente de desenvolvimento
cd deployments/docker
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml up

# Testar endpoints
curl http://localhost:8000/.well-known/jwks.json
curl http://localhost:8000/health/startup
curl http://localhost:8000/api/v1/examples/items
```

## Property Tests

Todos os módulos têm testes baseados em propriedades:

```bash
# Rodar todos os testes
uv run pytest tests/properties/test_api_best_practices_2025_*.py -v

# Resultados: 102 testes passando
```
