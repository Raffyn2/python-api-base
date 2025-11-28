# Implementation Plan

- [x] 1. Set up property-based test infrastructure
  - [x] 1.1 Create test file `tests/properties/test_file_size_compliance_phase2_properties.py`
    - Define REFACTORED_MODULES and REFACTORED_PACKAGES constants
    - Set up Hypothesis imports and settings
    - _Requirements: 6.1, 6.3_

  - [x] 1.2 Write property test for Public API Preservation
    - **Property 1: Public API Preservation**
    - **Validates: Requirements 5.1, 5.2, 5.3**

  - [x] 1.3 Write property test for File Size Compliance
    - **Property 2: File Size Compliance**
    - **Validates: Requirements 6.1**

  - [x] 1.4 Write property test for No Circular Imports
    - **Property 3: No Circular Imports**
    - **Validates: Requirements 6.3**

- [x] 2. Refactor High Priority Shared Modules (401-500 lines)
  - [x] 2.1 Refactor waf.py (482 lines) to `waf/` package
    - Create `waf/enums.py` with ThreatType, RuleAction, RuleSeverity
    - Create `waf/models.py` with WAFRule, ThreatDetection, WAFRequest, WAFResponse
    - Create `waf/patterns.py` with SQL_INJECTION_PATTERNS, XSS_PATTERNS, etc.
    - Create `waf/engine.py` with WAFRuleEngine
    - Create `waf/middleware.py` with WAFMiddleware, create_waf_middleware
    - Create `waf/__init__.py` with re-exports
    - Remove original waf.py
    - _Requirements: 1.1, 5.1, 5.2, 5.3_

  - [x] 2.2 Refactor hot_reload.py (479 lines) to `hot_reload/` package
    - Create `hot_reload/watcher.py` with file watching logic
    - Create `hot_reload/handler.py` with reload handlers
    - Create `hot_reload/config.py` with configuration
    - Create `hot_reload/__init__.py` with re-exports
    - Remove original hot_reload.py
    - _Requirements: 1.2, 5.1, 5.2, 5.3_

  - [x] 2.3 Refactor auto_ban.py (475 lines) to `auto_ban/` package
    - Create `auto_ban/detector.py` with detection logic
    - Create `auto_ban/store.py` with ban storage
    - Create `auto_ban/config.py` with configuration
    - Create `auto_ban/__init__.py` with re-exports
    - Remove original auto_ban.py
    - _Requirements: 1.3, 5.1, 5.2, 5.3_

  - [x] 2.4 Refactor csp_generator.py (475 lines) to `csp_generator/` package
    - Create `csp_generator/directives.py` with CSP directives
    - Create `csp_generator/builder.py` with policy builder
    - Create `csp_generator/policy.py` with policy classes
    - Create `csp_generator/__init__.py` with re-exports
    - Remove original csp_generator.py
    - _Requirements: 1.4, 5.1, 5.2, 5.3_

  - [x] 2.5 Refactor lazy.py (465 lines) to `lazy/` package
    - Create `lazy/proxy.py` with lazy proxy classes
    - Create `lazy/loader.py` with loading logic
    - Create `lazy/cache.py` with caching
    - Create `lazy/__init__.py` with re-exports
    - Remove original lazy.py
    - _Requirements: 1.5, 5.1, 5.2, 5.3_

  - [x] 2.6 Refactor fingerprint.py (462 lines) to `fingerprint/` package
    - Create `fingerprint/generators.py` with fingerprint generation
    - Create `fingerprint/validators.py` with validation logic
    - Create `fingerprint/store.py` with storage
    - Create `fingerprint/__init__.py` with re-exports
    - Remove original fingerprint.py
    - _Requirements: 1.6, 5.1, 5.2, 5.3_

- [x] 3. Checkpoint - Verify High Priority Refactoring
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Refactor Medium Priority Shared Modules (Part 1: 440-460 lines)
  - [x] 4.1 Refactor query_analyzer.py (457 lines) to `query_analyzer/` package
    - Create analyzer, metrics, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.1, 5.1, 5.2, 5.3_

  - [x] 4.2 Refactor protocols.py (452 lines) to `protocols/` package
    - Create base, http, websocket modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.2, 5.1, 5.2, 5.3_

  - [x] 4.3 Refactor multitenancy.py (451 lines) to `multitenancy/` package
    - Create tenant, resolver, middleware modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.3, 5.1, 5.2, 5.3_

  - [x] 4.4 Refactor background_tasks.py (447 lines) to `background_tasks/` package
    - Create scheduler, worker, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.4, 5.1, 5.2, 5.3_

- [x] 5. Refactor Medium Priority Shared Modules (Part 2: 420-440 lines)
  - [x] 5.1 Refactor http2_config.py (439 lines) to `http2_config/` package
    - Create settings, push, middleware modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.5, 5.1, 5.2, 5.3_

  - [x] 5.2 Refactor connection_pool.py (438 lines) to `connection_pool/` package
    - Create pool, manager, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.6, 5.1, 5.2, 5.3_

  - [x] 5.3 Refactor memory_profiler.py (435 lines) to `memory_profiler/` package
    - Create profiler, tracker, reporter modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.7, 5.1, 5.2, 5.3_

  - [x] 5.4 Refactor bff.py (428 lines) to `bff/` package
    - Create aggregator, transformer, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.8, 5.1, 5.2, 5.3_

  - [x] 5.5 Refactor request_signing.py (427 lines) to `request_signing/` package
    - Create signer, verifier, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.9, 5.1, 5.2, 5.3_

- [x] 6. Checkpoint - Verify Medium Priority Part 1 & 2
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Refactor Medium Priority Shared Modules (Part 3: 400-425 lines)
  - [x] 7.1 Refactor feature_flags.py (424 lines) to `feature_flags/` package
    - Create flags, evaluator, store modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.10, 5.1, 5.2, 5.3_

  - [x] 7.2 Refactor streaming.py (424 lines) to `streaming/` package
    - Create stream, chunker, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.11, 5.1, 5.2, 5.3_

  - [x] 7.3 Refactor api_composition.py (406 lines) to `api_composition/` package
    - Create composer, aggregator, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.12, 5.1, 5.2, 5.3_

  - [x] 7.4 Refactor response_transformation.py (406 lines) to `response_transformation/` package
    - Create transformer, filters, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.13, 5.1, 5.2, 5.3_

  - [x] 7.5 Refactor mutation_testing.py (403 lines) to `mutation_testing/` package
    - Create mutator, runner, reporter modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.14, 5.1, 5.2, 5.3_

  - [x] 7.6 Refactor graphql_federation.py (401 lines) to `graphql_federation/` package
    - Create schema, resolver, gateway modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 2.15, 5.1, 5.2, 5.3_

- [x] 8. Fix Import Errors in Refactored Packages
  - [x] 8.1 Fix api_composition/constants.py missing TypeVar import
    - Add `from typing import TypeVar` import
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.2 Fix response_transformation/service.py missing InputT/OutputT TypeVars
    - Add TypeVar definitions for InputT and OutputT
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.3 Fix connection_pool/constants.py missing TypeVar import
    - Add `from typing import TypeVar` import
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.4 Fix http2_config/config.py circular import with PushResource
    - Use TYPE_CHECKING and lazy import
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.5 Fix background_tasks/models.py missing T TypeVar and TaskConfig
    - Move TaskConfig to models.py to resolve circular import
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.6 Fix background_tasks/constants.py missing TypeVar import
    - Add `from typing import TypeVar` import
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.7 Fix multitenancy/constants.py missing TypeVar import
    - Add `from typing import TypeVar` import
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.8 Fix multitenancy/service.py missing CreateT/UpdateT TypeVars
    - Add TypeVar definitions for CreateT and UpdateT
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.9 Fix protocols/entities.py missing Identifiable import
    - Add import from base module
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

  - [x] 8.10 Split telemetry/service.py to comply with 400 line limit
    - Extract NoOp classes to noop.py
    - _Requirements: 6.1, 5.1, 5.2, 5.3_

  - [x] 8.11 Verify all packages import correctly
    - Run property tests to confirm no import errors
    - _Requirements: 5.1, 5.2, 5.3, 6.3_

- [x] 9. Checkpoint - Verify All Shared Module Refactoring
  - All 9 property tests pass

- [x] 10. Refactor Infrastructure Modules
  - [x] 10.1 Refactor token_store.py (473 lines) to `token_store/` package
    - Create store, models, cache modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 3.1, 5.1, 5.2, 5.3_

  - [x] 10.2 Refactor telemetry.py (422 lines) to `telemetry/` package
    - Create exporters, collectors, config modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 3.2, 5.1, 5.2, 5.3_

- [x] 11. Refactor Adapter Modules
  - [x] 11.1 Refactor websocket/types.py (473 lines) to `websocket/types/` package
    - Create messages, events, handlers modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 4.1, 5.1, 5.2, 5.3_

  - [x] 11.2 Refactor routes/auth.py (425 lines) to `routes/auth/` package
    - Create handlers, schemas, dependencies modules
    - Create `__init__.py` with re-exports
    - Remove original file
    - _Requirements: 4.2, 5.1, 5.2, 5.3_

- [x] 12. Final Checkpoint - Verify All Refactoring Complete
  - All 9 property tests pass
  - All 25 modules refactored to packages
  - All files under 400 lines
  - All imports working correctly
  - Backward compatibility maintained via __init__.py re-exports
