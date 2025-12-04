# ADR-017: File Size Refactoring - December 2025

## Status

Accepted

## Context

Code review identified 5 files exceeding the 400-line threshold defined in project standards:

| File | Lines | Issue |
|------|-------|-------|
| `src/interface/graphql/schema.py` | 547 | Monolithic GraphQL schema |
| `src/core/di/container.py` | 453 | Container + metrics in single file |
| `src/interface/v1/examples/router.py` | 442 | All routes + dependencies mixed |
| `src/application/common/middleware/observability.py` | 425 | 3 middlewares in one file |
| `src/infrastructure/resilience/patterns.py` | 408 | 5 patterns in one file |

Standards mandate: Files 200-400 max 500 lines, one class per file where practical.

## Decision

Split each file into focused, single-responsibility modules while maintaining backward compatibility through re-exports.

### 1. GraphQL Schema (547 → 6 files)

```
src/interface/graphql/
├── schema.py          (19 lines - entry point)
├── queries.py         (115 lines)
├── mutations.py       (160 lines)
├── mappers.py         (130 lines)
└── types/
    ├── __init__.py
    ├── shared_types.py
    ├── item_types.py
    └── pedido_types.py
```

### 2. DI Container (453 → 2 files)

```
src/core/di/
├── container.py       (210 lines - core logic)
└── metrics.py         (115 lines - stats + hooks)
```

### 3. Examples Router (442 → 4 files)

```
src/interface/v1/examples/
├── router.py          (45 lines - aggregator)
├── dependencies.py    (150 lines)
├── item_routes.py     (160 lines)
└── pedido_routes.py   (155 lines)
```

### 4. Observability Middleware (425 → 4 files)

```
src/application/common/middleware/
├── observability.py        (50 lines - re-exports)
├── logging_middleware.py   (130 lines)
├── idempotency_middleware.py (145 lines)
└── metrics_middleware.py   (150 lines)
```

### 5. Resilience Patterns (408 → 6 files)

```
src/infrastructure/resilience/
├── patterns.py         (35 lines - re-exports)
├── circuit_breaker.py  (220 lines)
├── retry_pattern.py    (95 lines)
├── timeout.py          (50 lines)
├── fallback.py         (45 lines)
└── bulkhead.py         (60 lines)
```

## Consequences

### Positive

- All files now under 400 lines
- Single Responsibility Principle enforced
- Easier to test individual components
- Better IDE navigation and code discovery
- Reduced merge conflicts in team development

### Negative

- More files to navigate
- Import paths may need updates in consuming code

### Neutral

- Backward compatibility maintained via re-exports
- No API changes for external consumers

## Alternatives Rejected

1. **Keep large files with regions**: Rejected - doesn't solve SRP violations
2. **Partial splits**: Rejected - inconsistent approach
3. **Monorepo packages**: Rejected - over-engineering for current scale

## Verification

```bash
# Confirm no files exceed 400 lines
Get-ChildItem -Path src -Recurse -Filter "*.py" | 
  ForEach-Object { 
    $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
    if ($lines -gt 400) { Write-Host "$($_.FullName): $lines lines" }
  }
# Result: No output (all files compliant)
```

## References

- Project Standards: agent.md (STANDARDS.Sizes)
- Clean Code: Chapter 10 - Classes
- SOLID Principles: Single Responsibility
