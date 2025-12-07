# Design Document

## Overview

Este design define a estratégia para alcançar cobertura de testes realista (60-65% global) focando nas camadas de maior valor do projeto Python API Base.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Coverage Strategy                    │
├─────────────────────────────────────────────────────────────┤
│  Layer          │ Lines  │ Target │ Priority │ Test Type   │
├─────────────────────────────────────────────────────────────┤
│  Core           │ ~2000  │  85%+  │  HIGH    │ Unit        │
│  Domain         │ ~2000  │  80%+  │  HIGH    │ Unit        │
│  Application    │ ~3000  │  70%+  │  MEDIUM  │ Unit        │
│  Infrastructure │ ~15000 │  OMIT  │  LOW     │ Integration │
│  Interface      │ ~4000  │  OMIT  │  LOW     │ E2E         │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Coverage Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = [
    "src/interface/*",
    "src/infrastructure/dapr/*",
    "src/infrastructure/grpc/*",
    "src/infrastructure/kafka/*",
    "src/infrastructure/elasticsearch/*",
    "src/infrastructure/scylladb/*",
    "src/main.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Test Organization

```
tests/
├── unit/
│   ├── core/           # 85%+ coverage target
│   │   ├── base/
│   │   ├── config/
│   │   ├── di/
│   │   ├── errors/
│   │   ├── shared/
│   │   └── core_types/
│   ├── domain/         # 80%+ coverage target
│   │   ├── common/
│   │   ├── users/
│   │   └── examples/
│   └── application/    # 70%+ coverage target
│       └── common/
└── integration/        # Future: external services
```

## Data Models

N/A - Este spec foca em testes, não em modelos de dados.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Coverage Threshold Compliance
*For any* test run with coverage, the reported coverage for Core layer SHALL be >= 85%
**Validates: Requirements 1.1**

### Property 2: Domain Coverage Compliance
*For any* test run with coverage, the reported coverage for Domain layer SHALL be >= 80%
**Validates: Requirements 1.2**

### Property 3: Application Coverage Compliance
*For any* test run with coverage, the reported coverage for Application layer SHALL be >= 70%
**Validates: Requirements 1.3**

### Property 4: Test Suite Stability
*For any* test run, all unit tests SHALL pass without failures or timeouts
**Validates: Requirements 3.1, 3.2**

## Error Handling

- Testes que falham devem ser corrigidos ou marcados com `pytest.mark.skip` com justificativa
- Testes que dependem de serviços externos devem estar em `tests/integration/`
- Timeouts devem ser investigados e resolvidos

## Performance Benchmarks

### Benchmark Strategy
- Usar pytest-benchmark para medições consistentes
- Estabelecer baselines para operações críticas
- Detectar regressões em CI/CD

### Targets
| Operation | Target | Measurement |
|-----------|--------|-------------|
| DTO Serialization | <1ms/1000 items | model_dump_json() |
| Validation | >10k/sec | validate() calls |
| Cache Operations | <0.1ms/op | get/set operations |

## Testing Strategy

### Unit Testing
- pytest como framework principal
- pytest-cov para cobertura
- pytest-asyncio para testes assíncronos
- Mocks apenas para dependências internas, não para serviços externos

### Coverage Measurement
```bash
# Comando para medir cobertura com exclusões
uv run pytest tests/unit/ --cov=src --cov-report=term-missing \
    --ignore=tests/unit/infrastructure/db/test_query_timing_prometheus.py
```

### Property-Based Testing
- hypothesis para testes de propriedades
- Foco em DTOs, serialização, e validação

