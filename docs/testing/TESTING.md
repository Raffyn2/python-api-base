# Testing Strategy

## Overview

This document describes the testing strategy for the Python API Base project, targeting 60-65% global coverage with focus on high-value layers.

## Coverage Targets by Layer

| Layer | Target | Priority | Test Type |
|-------|--------|----------|-----------|
| Core | 85%+ | HIGH | Unit |
| Domain | 80%+ | HIGH | Unit |
| Application | 70%+ | MEDIUM | Unit |
| Infrastructure | OMIT | LOW | Integration |
| Interface | OMIT | LOW | E2E |

## Test Organization

```
tests/
├── unit/           # Unit tests (fast, isolated)
│   ├── core/       # Core layer tests
│   ├── domain/     # Domain layer tests
│   ├── application/# Application layer tests
│   └── infrastructure/ # Infrastructure unit tests
├── integration/    # Integration tests
├── properties/     # Property-based tests (Hypothesis)
├── e2e/           # End-to-end tests
├── contract/      # Contract tests
├── performance/   # Performance benchmarks
└── factories/     # Test factories and fixtures
```

## Coverage Exclusions

The following modules are excluded from coverage metrics:

- `src/interface/*` - Requires running server, better for E2E tests
- `src/infrastructure/dapr/*` - Requires Dapr sidecar
- `src/infrastructure/grpc/*` - Requires gRPC server
- `src/infrastructure/kafka/*` - Requires Kafka broker
- `src/infrastructure/elasticsearch/*` - Requires Elasticsearch
- `src/infrastructure/scylladb/*` - Requires ScyllaDB
- `src/main.py` - Application entry point

### Rationale

These exclusions exist because:
1. External service adapters require running infrastructure
2. Interface layer is better tested via E2E tests
3. Entry points have minimal logic

## Running Tests

```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/unit/ --cov=src --cov-report=term-missing

# Run specific layer
uv run pytest tests/unit/core/ -v
uv run pytest tests/unit/domain/ -v
uv run pytest tests/unit/application/ -v

# Run property tests
uv run pytest tests/properties/ -v

# Run integration tests
uv run pytest tests/integration/ -v
```

## Test Fixtures

Shared fixtures are located in:
- `tests/conftest.py` - Global fixtures
- `tests/factories/` - Test factories and strategies

### Key Fixtures

- `entity_factory.py` - Generic entity factories
- `hypothesis_strategies.py` - Hypothesis strategies for property tests
- `mock_repository.py` - Mock repository implementations

## Property-Based Testing

We use Hypothesis for property-based testing. Key properties tested:

1. **Serialization Round-Trip** - DTOs serialize/deserialize correctly
2. **Validation Consistency** - Validators behave consistently
3. **ID Uniqueness** - Generated IDs are unique
4. **Immutability** - Value objects are immutable

## Best Practices

1. **Test Isolation** - Each test should be independent
2. **Fast Tests** - Unit tests should run in milliseconds
3. **Clear Names** - Test names should describe the scenario
4. **Arrange-Act-Assert** - Follow AAA pattern
5. **No Mocks for External Services** - Use integration tests instead
