# ADR-021: Security Hardening 2025

## Status

Accepted

## Date

2025-12-04

## Context

Durante code review sistemático, foram identificadas oportunidades de hardening de segurança:

1. **CORS Wildcard**: Configuração permitia `*` em produção apenas com warning
2. **JWT Algorithm Default**: HS256 como padrão, menos seguro que algoritmos assimétricos
3. **Cache Key Collision**: Hash SHA256 truncado para 8 caracteres
4. **DI Provider Evaluation**: Lambdas em `providers.Callable` avaliadas em cada acesso

## Decision

### 1. CORS Blocking em Produção

```python
# ANTES: Apenas warning
if "*" in v and env == "production":
    logger.warning("SECURITY WARNING...")

# DEPOIS: Bloqueia em produção
if "*" in v and env == "production":
    raise ValueError("Wildcard CORS origin '*' not allowed in production")
```

### 2. JWT Default para RS256

```python
# ANTES
algorithm: str = "HS256"
require_secure_algorithm: bool = False

# DEPOIS
algorithm: str = "RS256"
require_secure_algorithm: bool = True
```

### 3. Cache Key Hash Expandido

```python
# ANTES: 8 caracteres (2^32 combinações)
key_hash = hashlib.sha256(...).hexdigest()[:8]

# DEPOIS: 16 caracteres (2^64 combinações)
key_hash = hashlib.sha256(...).hexdigest()[:16]
```

### 4. DI Provider Optimization

```python
# ANTES: providers.Callable (avaliado em cada acesso)
# DEPOIS: providers.Factory (avaliado uma vez por singleton)
```

## Consequences

### Positive

- CORS wildcard bloqueado em produção previne CSRF
- RS256 default melhora segurança de tokens (chaves assimétricas)
- Redução de colisões de cache key de 1:4B para 1:18Q
- Performance melhorada no DI container

### Negative

- Breaking change para quem usa CORS `*` em produção (intencional)
- Requer configuração de chaves RSA/EC para JWT em produção

### Neutral

- Backward compatible para ambientes não-produção
- Testes existentes continuam passando

## Alternatives Considered

1. **Manter warnings**: Rejeitado - não previne configuração insegura
2. **SHA256 completo para cache**: Rejeitado - overhead desnecessário
3. **Forçar RS256 sempre**: Rejeitado - quebra desenvolvimento local

## References

- OWASP CORS Security: https://owasp.org/www-community/attacks/CORS_OriginHeaderScrutiny
- JWT Best Practices RFC 8725: https://datatracker.ietf.org/doc/html/rfc8725
- Birthday Problem (hash collisions): https://en.wikipedia.org/wiki/Birthday_problem
