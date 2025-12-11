# Design Document: Code Quality Fixes

## Overview

This design document outlines the approach to fix all code quality issues identified in the Python API Base project. The fixes are organized into phases: configuration fixes, module structure fixes, automated formatting/linting, and verification. The approach prioritizes automated fixes where possible and manual intervention only where necessary.

## Architecture

The fix strategy follows a layered approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 1: Configuration                    │
│  - Update pyproject.toml (mypy python_version → 3.13)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Phase 2: Module Structure                    │
│  - Create missing modules (infrastructure.dapr.errors)       │
│  - Fix circular imports (eventing.cloudevents)              │
│  - Fix missing exports (FieldError, TimeoutError)           │
│  - Rename conflicting test directories                       │
│  - Fix missing imports in test files                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 3: Automated Fixes                        │
│  - Run ruff format . (fix 1438 files)                       │
│  - Run ruff check . --fix (fix safe linting issues)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 4: Manual Fixes                           │
│  - Fix remaining linting issues not auto-fixable            │
│  - Fix broken import paths in test files                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 5: Verification                           │
│  - Run full validation suite                                 │
│  - Ensure all checks pass                                    │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Configuration Component (pyproject.toml)

**Current Issue:**
```toml
[tool.mypy]
python_version = "3.12"  # Incorrect - project uses Python 3.13
```

**Fix:**
```toml
[tool.mypy]
python_version = "3.13"  # Match runtime version
```

### 2. Missing Module: infrastructure.dapr.errors

**Location:** `src/infrastructure/dapr/errors.py`

**Required Exports:**
- `DaprConnectionError` - Exception for connection failures
- `DaprTimeoutError` - Exception for timeout errors
- `DaprError` - Base exception class

### 3. Circular Import Fix: eventing.cloudevents

**Current Issue:** `src/infrastructure/eventing/__init__.py` imports from `cloudevents.dependencies` which imports from `cloudevents.models` which triggers circular import.

**Fix Strategy:** Use lazy imports or restructure the `__init__.py` to avoid importing from dependencies at module level.

### 4. Missing Export: FieldError

**Location:** `src/interface/errors/exceptions.py`

**Current Issue:** `FieldError` is only imported under `TYPE_CHECKING`, not exported at runtime.

**Fix:** Import and re-export `FieldError` unconditionally.

### 5. Missing Export: TimeoutError

**Location:** `src/infrastructure/grpc/utils/status.py`

**Required:** Export a `TimeoutError` class for gRPC timeout handling.

### 6. Test Directory Conflicts

**Issue:** `tests/unit/interface/graphql/` and `tests/unit/interface/grpc/` conflict with installed packages `graphql` and `grpc`.

**Fix:** Rename directories to `graphql_tests/` and `grpc_tests/` or add `__init__.py` files with proper package markers.

### 7. Missing pytest Import

**Location:** `tests/unit/test_health.py`

**Fix:** Add `import pytest` at the top of the file.

### 8. Broken Import Paths

**Files Affected:**
- `tests/integration/test_batch_operations.py` - Wrong import path for BatchOperationBuilder
- `tests/integration/test_user_crud.py` - Wrong import for User class

## Data Models

No new data models are required. This is a code quality fix that modifies existing code structure.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis, most acceptance criteria are verifiable through example-based testing (running commands and checking results). The key properties are:

**Property 1: Type checker passes**
*For any* valid Python source file in src/, running mypy SHALL produce zero type errors.
**Validates: Requirements 1.1, 1.2, 1.3**

**Property 2: Test collection succeeds**
*For any* test file in tests/, pytest collection SHALL succeed without import errors.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 5.1**

**Property 3: Linting passes**
*For any* Python source file in the project, ruff check SHALL report zero errors.
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

**Property 4: Formatting is consistent**
*For any* Python source file in the project, ruff format --check SHALL report the file as already formatted.
**Validates: Requirements 3.1, 3.2**

## Error Handling

- If automated fixes introduce new errors, revert and apply manual fixes
- If module creation breaks existing imports, update all dependent files
- If test directory renaming breaks CI, update CI configuration accordingly

## Testing Strategy

### Verification Approach

Since this is a code quality fix, testing is done through validation commands:

1. **Type Checking:** `uv run mypy src/` - Must exit with code 0
2. **Test Collection:** `uv run pytest --collect-only tests/` - Must report 0 errors
3. **Linting:** `uv run ruff check .` - Must exit with code 0
4. **Formatting:** `uv run ruff format --check .` - Must exit with code 0
5. **Full Test Suite:** `uv run pytest tests/` - Must collect and run all tests

### Property-Based Testing

Property-based tests are not applicable for this feature as it involves code quality fixes rather than functional behavior. The correctness properties are verified through the validation commands above.

### Validation Checkpoints

After each phase, run the relevant validation command to ensure no regressions:
- Phase 1: `uv run mypy src/`
- Phase 2: `uv run pytest --collect-only tests/`
- Phase 3: `uv run ruff check .` and `uv run ruff format --check .`
- Phase 4: All commands
- Phase 5: Full validation suite
