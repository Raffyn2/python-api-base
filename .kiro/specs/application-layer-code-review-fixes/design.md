# Design: Application Layer Code Review Fixes

**Feature**: application-layer-code-review-fixes
**Status**: Proposed

## Overview

Este documento detalha o design técnico para correção dos 5 findings identificados no code review da camada `src/application`.

---

## F-01: Tenant ID Validation Hardening

### Current State

```python
# src/application/services/multitenancy/middleware.py:89-103
def _sanitize_tenant_id(self, tenant_id: str) -> str | None:
    if len(tenant_id) > TENANT_ID_MAX_LENGTH:
        # ... reject
        return None
    
    if not TENANT_ID_PATTERN.match(tenant_id):
        # ... reject
        return None
    
    return tenant_id
```

### Problem

- Tenant ID `"   "` (whitespace-only) passa na validação de length
- Regex `^[a-zA-Z0-9_-]{1,64}$` rejeita, mas sem log específico
- Tenant ID `""` (vazio) passa direto sem validação

### Solution

```python
def _sanitize_tenant_id(self, tenant_id: str) -> str | None:
    """Sanitize tenant ID to prevent injection attacks."""
    # Strip whitespace first
    tenant_id = tenant_id.strip()
    
    # Reject empty after strip
    if not tenant_id:
        logger.warning(
            "Tenant ID rejected: empty or whitespace-only",
            extra={
                "operation": "TENANT_VALIDATION",
                "reason": "EMPTY_OR_WHITESPACE",
            },
        )
        return None
    
    # Existing validations...
    if len(tenant_id) > TENANT_ID_MAX_LENGTH:
        logger.warning(
            "Tenant ID rejected: exceeds max length",
            extra={
                "operation": "TENANT_VALIDATION",
                "reason": "LENGTH_EXCEEDED",
            },
        )
        return None

    if not TENANT_ID_PATTERN.match(tenant_id):
        logger.warning(
            "Tenant ID rejected: invalid characters",
            extra={"operation": "TENANT_VALIDATION", "reason": "INVALID_CHARS"},
        )
        return None

    return tenant_id
```

### Impact

- **Security**: Previne bypass de tenant isolation
- **Breaking Changes**: Nenhum (apenas rejeita inputs inválidos)
- **Tests**: Adicionar casos para `""`, `"   "`, `" valid "` (trimmed)

---

## F-02: Batch Repository Deep Copy Safety

### Current State

```python
# src/application/common/batch/repository.py:85
snapshot = (
    {k: self._entity_type.model_validate(v.model_dump()) for k, v in self._storage.items()}
    if cfg.error_strategy == BatchErrorStrategy.ROLLBACK
    else None
)
```

### Problem

- `model_dump()` pode falhar com tipos não-serializáveis (datetime sem encoder, custom objects)
- Sem fallback, rollback falha silenciosamente

### Solution

```python
import copy

def _create_snapshot(self) -> dict[str, T]:
    """Create deep copy of storage for rollback.
    
    Uses Pydantic serialization when possible, falls back to deepcopy
    for complex types that don't serialize cleanly.
    """
    try:
        return {
            k: self._entity_type.model_validate(v.model_dump())
            for k, v in self._storage.items()
        }
    except Exception as e:
        logger.warning(
            f"Pydantic snapshot failed, using deepcopy: {e}",
            extra={"operation": "BATCH_SNAPSHOT"},
        )
        return copy.deepcopy(self._storage)
```

### Usage in bulk_create

```python
snapshot = (
    self._create_snapshot()
    if cfg.error_strategy == BatchErrorStrategy.ROLLBACK
    else None
)
```

### Impact

- **Reliability**: Rollback funciona com qualquer tipo de entidade
- **Performance**: Deepcopy é mais lento, mas só usado como fallback
- **Breaking Changes**: Nenhum

---

## F-03: Kafka Publishing DRY Refactoring

### Current State

Código duplicado 3x em `create()`, `update()`, `delete()`:

```python
# Repetido em cada método
if self._kafka_publisher:
    try:
        from infrastructure.kafka.event_publisher import (
            DomainEvent,
            ItemCreatedEvent,  # ou ItemUpdatedEvent, ItemDeletedEvent
        )
        kafka_event = DomainEvent(
            event_type="ItemCreated",
            entity_type="ItemExample",
            entity_id=saved.id,
            payload=ItemCreatedEvent(...),
        )
        await self._kafka_publisher.publish(kafka_event, "items-events")
    except Exception as e:
        logger.error(f"Failed to publish Kafka event: {e}")
```

### Solution

```python
async def _publish_kafka_event(
    self,
    event_type: str,
    entity_id: str,
    payload: Any,
    topic: str = "items-events",
) -> None:
    """Publish domain event to Kafka.
    
    Centralizes Kafka event publishing with consistent error handling.
    
    Args:
        event_type: Type of event (ItemCreated, ItemUpdated, ItemDeleted)
        entity_id: ID of the affected entity
        payload: Event-specific payload dataclass
        topic: Kafka topic (default: items-events)
    """
    if not self._kafka_publisher:
        return
    
    try:
        from infrastructure.kafka.event_publisher import DomainEvent
        
        kafka_event = DomainEvent(
            event_type=event_type,
            entity_type="ItemExample",
            entity_id=entity_id,
            payload=payload,
        )
        await self._kafka_publisher.publish(kafka_event, topic)
        
        logger.debug(
            f"Kafka event published: {event_type}",
            extra={
                "event_type": event_type,
                "entity_id": entity_id,
                "topic": topic,
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to publish Kafka event: {e}",
            extra={
                "event_type": event_type,
                "entity_id": entity_id,
                "error": str(e),
            },
        )
```

### Usage

```python
# Em create()
await self._publish_kafka_event(
    event_type="ItemCreated",
    entity_id=saved.id,
    payload=ItemCreatedEvent(
        id=saved.id,
        name=saved.name,
        sku=saved.sku,
        quantity=saved.quantity,
        created_by=created_by,
    ),
)

# Em update()
await self._publish_kafka_event(
    event_type="ItemUpdated",
    entity_id=saved.id,
    payload=ItemUpdatedEvent(
        id=saved.id,
        changes=changes,
        updated_by=updated_by,
    ),
)

# Em delete()
await self._publish_kafka_event(
    event_type="ItemDeleted",
    entity_id=item_id,
    payload=ItemDeletedEvent(
        id=item_id,
        deleted_by=deleted_by,
    ),
)
```

### Impact

- **Maintainability**: Lógica centralizada, fácil de modificar
- **Lines Reduced**: ~45 linhas → ~15 linhas (3 chamadas)
- **Breaking Changes**: Nenhum (refatoração interna)

---

## F-04: User Mapper Password Hash Validation

### Current State

```python
# src/application/users/commands/mapper.py:55
def to_entity(self, dto: UserDTO) -> UserAggregate:
    return UserAggregate(
        # ...
        password_hash="",  # Not stored in DTO for security
    )
```

### Problem

- Cria aggregate com password_hash vazio sem warning
- Pode ser usado incorretamente para criar novos usuários

### Solution

```python
def to_entity(
    self,
    dto: UserDTO,
    *,
    password_hash: str | None = None,
    _reconstitution: bool = True,
) -> UserAggregate:
    """Convert UserDTO to UserAggregate.

    WARNING: This method is for reconstitution from persistence only.
    For new user creation, use UserAggregate.create() directly.

    Args:
        dto: UserDTO to convert.
        password_hash: Optional password hash for migration scenarios.
        _reconstitution: Internal flag, always True for this method.

    Returns:
        UserAggregate with all DTO fields mapped.

    Raises:
        ValueError: If dto is None.
        TypeError: If dto is not a UserDTO.
    """
    if dto is None:
        raise ValueError("dto parameter cannot be None")
    if not isinstance(dto, UserDTO):
        raise TypeError(f"Expected UserDTO instance, got {type(dto).__name__}")

    if password_hash is None and _reconstitution:
        logger.debug(
            "Creating UserAggregate without password_hash (reconstitution mode)",
            extra={"user_id": dto.id, "operation": "USER_RECONSTITUTION"},
        )

    return UserAggregate(
        id=dto.id,
        email=dto.email,
        password_hash=password_hash or "",
        username=dto.username,
        display_name=dto.display_name,
        is_active=dto.is_active,
        is_verified=dto.is_verified,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        last_login_at=dto.last_login_at,
    )
```

### Impact

- **Security Awareness**: Documentação clara do uso correto
- **Flexibility**: Permite passar password_hash em migrações
- **Breaking Changes**: Nenhum (parâmetro opcional)

---

## F-05: Query Cache Pattern Matching (Documentation Only)

### Current State

Já otimizado com prefix matching:

```python
# src/application/common/middleware/query_cache.py:95
if pattern.endswith("*") and "*" not in pattern[:-1] and "?" not in pattern:
    prefix = pattern[:-1]
    matching_keys = [key for key in self._cache if key.startswith(prefix)]
else:
    import fnmatch
    matching_keys = [key for key in self._cache if fnmatch.fnmatch(key, pattern)]
```

### Solution

Apenas adicionar documentação de performance:

```python
async def clear_pattern(self, pattern: str) -> int:
    """Clear cached results matching pattern.

    Supports * wildcard for pattern matching.
    Optimized for common prefix patterns (e.g., "prefix:*").

    Performance Characteristics:
    - Prefix patterns ("prefix:*"): O(n) with fast startswith
    - Complex patterns ("*mid*"): O(n*m) with fnmatch
    - For caches >10k keys, consider Redis SCAN for production
    
    Args:
        pattern: Pattern to match keys (e.g., "query_cache:GetUserQuery:*").

    Returns:
        Number of keys cleared.
    """
```

### Impact

- **Documentation**: Clareza sobre performance
- **Breaking Changes**: Nenhum

---

## Test Strategy

### Unit Tests Required

1. **F-01**: `test_tenant_validation_edge_cases.py`
   - `test_empty_tenant_id_rejected`
   - `test_whitespace_only_tenant_id_rejected`
   - `test_tenant_id_trimmed_before_validation`

2. **F-02**: `test_batch_repository_snapshot.py`
   - `test_snapshot_with_complex_types`
   - `test_snapshot_fallback_to_deepcopy`

3. **F-03**: `test_item_use_case_kafka.py`
   - `test_kafka_event_published_on_create`
   - `test_kafka_event_published_on_update`
   - `test_kafka_event_published_on_delete`
   - `test_kafka_error_logged_not_raised`

4. **F-04**: `test_user_mapper.py`
   - `test_to_entity_logs_reconstitution_warning`
   - `test_to_entity_with_password_hash`

---

## Rollout Plan

1. **Phase 1**: F-01 (Security) - Immediate
2. **Phase 2**: F-03, F-04 (Maintainability) - Sprint atual
3. **Phase 3**: F-02, F-05 (Reliability/Performance) - Próximo sprint

## Risks

| Risk | Mitigation |
|------|------------|
| F-01 pode rejeitar tenant IDs válidos com espaços | Trim antes de validar, não rejeitar |
| F-02 deepcopy pode ser lento | Só usado como fallback |
| F-03 refatoração pode quebrar eventos | Testes de integração existentes |
