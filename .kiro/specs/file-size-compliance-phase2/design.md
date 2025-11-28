# Design Document

## Overview

This design document outlines the technical approach for Phase 2 of the file size compliance initiative. The goal is to refactor 25 files exceeding the 400-line limit by extracting them into focused packages while maintaining backward compatibility.

The refactoring follows established patterns from Phase 1 (code-review-refactoring spec), using Python packages with `__init__.py` re-exports to preserve existing import paths.

## Architecture

### Current State

Files exceeding 400 lines are distributed across three layers:

```
src/my_api/
├── shared/           # 21 files (waf.py, hot_reload.py, auto_ban.py, etc.)
├── infrastructure/   # 2 files (token_store.py, telemetry.py)
└── adapters/         # 2 files (websocket/types.py, routes/auth.py)
```

### Target State

Each oversized file becomes a package with focused modules:

```
src/my_api/
├── shared/
│   ├── waf/
│   │   ├── __init__.py      # Re-exports for backward compatibility
│   │   ├── enums.py         # ThreatType, RuleAction, RuleSeverity
│   │   ├── models.py        # WAFRule, ThreatDetection, WAFRequest, WAFResponse
│   │   ├── patterns.py      # SQL_INJECTION_PATTERNS, XSS_PATTERNS, etc.
│   │   ├── engine.py        # WAFRuleEngine
│   │   └── middleware.py    # WAFMiddleware, create_waf_middleware
│   └── [other packages...]
├── infrastructure/
│   ├── auth/
│   │   └── token_store/     # Package replaces token_store.py
│   └── observability/
│       └── telemetry/       # Package replaces telemetry.py
└── adapters/api/
    ├── websocket/
    │   └── types/           # Package replaces types.py
    └── routes/
        └── auth/            # Package replaces auth.py
```

## Components and Interfaces

### Package Structure Pattern

Each refactored module follows this standard structure:

```python
# package/__init__.py
"""Module description with feature reference.

**Feature: file-size-compliance-phase2, Task X.Y**
**Validates: Requirements N.M**
"""

from .enums import EnumA, EnumB
from .models import ModelA, ModelB
from .config import ConfigClass
from .service import ServiceClass, factory_function

__all__ = [
    "EnumA",
    "EnumB", 
    "ModelA",
    "ModelB",
    "ConfigClass",
    "ServiceClass",
    "factory_function",
]
```

### Module Decomposition Strategy

| Component Type | Target Module | Responsibility |
|---------------|---------------|----------------|
| Enums | `enums.py` | Type-safe constants and status values |
| Models | `models.py` | Data classes, DTOs, value objects |
| Config | `config.py` | Configuration classes and defaults |
| Service | `service.py` or domain-specific | Core business logic |
| Factory | `factory.py` | Object creation and builders |
| Middleware | `middleware.py` | Request/response processing |

### Shared Module Packages (High Priority)

| Original File | Package | Modules |
|--------------|---------|---------|
| waf.py (482) | `waf/` | enums, models, patterns, engine, middleware |
| hot_reload.py (479) | `hot_reload/` | watcher, handler, config |
| auto_ban.py (475) | `auto_ban/` | detector, store, config |
| csp_generator.py (475) | `csp_generator/` | directives, builder, policy |
| lazy.py (465) | `lazy/` | proxy, loader, cache |
| fingerprint.py (462) | `fingerprint/` | generators, validators, store |

### Shared Module Packages (Medium Priority)

| Original File | Package | Modules |
|--------------|---------|---------|
| query_analyzer.py (457) | `query_analyzer/` | analyzer, metrics, config |
| protocols.py (452) | `protocols/` | base, http, websocket |
| multitenancy.py (451) | `multitenancy/` | tenant, resolver, middleware |
| background_tasks.py (447) | `background_tasks/` | scheduler, worker, config |
| http2_config.py (439) | `http2_config/` | settings, push, middleware |
| connection_pool.py (438) | `connection_pool/` | pool, manager, config |
| memory_profiler.py (435) | `memory_profiler/` | profiler, tracker, reporter |
| bff.py (428) | `bff/` | aggregator, transformer, config |
| request_signing.py (427) | `request_signing/` | signer, verifier, config |
| feature_flags.py (424) | `feature_flags/` | flags, evaluator, store |
| streaming.py (424) | `streaming/` | stream, chunker, config |
| api_composition.py (406) | `api_composition/` | composer, aggregator, config |
| response_transformation.py (406) | `response_transformation/` | transformer, filters, config |
| mutation_testing.py (403) | `mutation_testing/` | mutator, runner, reporter |
| graphql_federation.py (401) | `graphql_federation/` | schema, resolver, gateway |

### Infrastructure Module Packages

| Original File | Package | Modules |
|--------------|---------|---------|
| token_store.py (473) | `token_store/` | store, models, cache |
| telemetry.py (422) | `telemetry/` | exporters, collectors, config |

### Adapter Module Packages

| Original File | Package | Modules |
|--------------|---------|---------|
| websocket/types.py (473) | `websocket/types/` | messages, events, handlers |
| routes/auth.py (425) | `routes/auth/` | handlers, schemas, dependencies |

## Data Models

No new data models are introduced. Existing models are relocated to appropriate modules within packages while preserving their structure and behavior.

### Model Migration Pattern

```python
# Before: shared/waf.py
@dataclass
class WAFRule:
    id: str
    name: str
    # ...

# After: shared/waf/models.py
@dataclass
class WAFRule:
    id: str
    name: str
    # ...

# After: shared/waf/__init__.py
from .models import WAFRule
__all__ = ["WAFRule", ...]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Public API Preservation

*For any* refactored module and *for any* symbol that was publicly exported before refactoring, importing that symbol from the original module path should succeed and return the same object.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 2: File Size Compliance

*For any* Python file within a refactored package, the file should contain 400 lines or fewer (excluding blank lines and comments in the count for functional code).

**Validates: Requirements 6.1**

### Property 3: No Circular Imports

*For any* module within a refactored package, importing that module should not raise an ImportError due to circular dependencies.

**Validates: Requirements 6.3**

## Error Handling

### Refactoring Errors

| Error Type | Handling Strategy |
|-----------|-------------------|
| Import failures | Verify all re-exports in `__init__.py` before committing |
| Circular imports | Use lazy imports or restructure dependencies |
| Missing symbols | Run `__all__` validation against original module |
| Type errors | Ensure all type hints are preserved |

### Validation Approach

```python
# Validation script pattern
def validate_refactoring(original_module: str, package_path: str) -> bool:
    """Validate that refactoring preserves public API."""
    original = importlib.import_module(original_module)
    refactored = importlib.import_module(package_path)
    
    original_symbols = set(getattr(original, '__all__', dir(original)))
    refactored_symbols = set(getattr(refactored, '__all__', dir(refactored)))
    
    return original_symbols <= refactored_symbols
```

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are used to ensure correctness:

- **Unit tests**: Verify specific refactoring scenarios and edge cases
- **Property-based tests**: Verify universal properties across all refactored modules

### Property-Based Testing Framework

- **Library**: Hypothesis (Python)
- **Minimum iterations**: 100 per property
- **Test location**: `tests/properties/test_file_size_compliance_phase2_properties.py`

### Property Test Specifications

#### Property 1: Public API Preservation Test

```python
@given(module_name=st.sampled_from(REFACTORED_MODULES))
@settings(max_examples=100)
def test_public_api_preserved(module_name: str) -> None:
    """
    **Feature: file-size-compliance-phase2, Property 1: Public API Preservation**
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    # Import original module symbols from __all__
    # Verify each symbol is accessible from package __init__.py
    pass
```

#### Property 2: File Size Compliance Test

```python
@given(package_path=st.sampled_from(REFACTORED_PACKAGES))
@settings(max_examples=100)
def test_file_size_compliance(package_path: str) -> None:
    """
    **Feature: file-size-compliance-phase2, Property 2: File Size Compliance**
    **Validates: Requirements 6.1**
    """
    # For each .py file in package
    # Assert line count <= 400
    pass
```

#### Property 3: No Circular Imports Test

```python
@given(module_path=st.sampled_from(ALL_NEW_MODULES))
@settings(max_examples=100)
def test_no_circular_imports(module_path: str) -> None:
    """
    **Feature: file-size-compliance-phase2, Property 3: No Circular Imports**
    **Validates: Requirements 6.3**
    """
    # Attempt to import module
    # Assert no ImportError raised
    pass
```

### Unit Test Coverage

Unit tests verify:
- Each refactored package exports all original symbols
- Factory functions create valid instances
- Configuration defaults are preserved
- Middleware chains work correctly after refactoring

### Integration Test Coverage

Existing integration tests should pass without modification, validating that:
- API endpoints using refactored modules work correctly
- Database operations remain functional
- Authentication flows are unaffected
