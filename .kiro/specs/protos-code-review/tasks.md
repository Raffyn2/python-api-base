# Implementation Plan

- [x] 1. Update buf configuration files
  - [x] 1.1 Update buf.yaml with STANDARD + COMMENTS lint rules
    - Add COMMENTS category to lint rules
    - Remove PACKAGE_VERSION_SUFFIX exception
    - Add protovalidate dependency
    - _Requirements: 1.1, 2.1-2.5, 6.3_
  - [x] 1.2 Update buf.gen.yaml with enhanced code generation
    - Add pyi plugin for type stubs
    - Add protovalidate-python plugin
    - Configure managed mode options
    - _Requirements: 6.1, 6.2, 6.5_

- [x] 2. Create common proto infrastructure
  - [x] 2.1 Create common/v1/pagination.proto
    - Define PageRequest message with page_size and page_token
    - Define PageResponse message with next_page_token, total_count, has_more
    - Add protovalidate constraints (page_size 1-100)
    - Add comprehensive documentation
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 2.3, 2.4_
  - [x] 2.2 Write property test for pagination structure
    - **Property 4: Pagination Structure Completeness**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 3. Refactor errors.proto to common/v1
  - [x] 3.1 Create common/v1/errors.proto with improvements
    - Add ErrorCode enum with semantic categories
    - Change timestamp field to google.protobuf.Timestamp
    - Add protovalidate constraints (UUID format, min_len)
    - Add comprehensive documentation for all elements
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 2.1-2.5_
  - [x] 3.2 Write property test for timestamp serialization
    - **Property 3: Timestamp Well-Known Types**
    - **Validates: Requirements 4.1, 4.3, 5.4**

- [x] 4. Refactor health.proto to common/v1
  - [x] 4.1 Move health.proto to common/v1 with version suffix
    - Update package to common.v1
    - Add comprehensive documentation
    - Ensure compatibility with grpc-health-checking
    - _Requirements: 9.1, 2.1-2.5_

- [x] 5. Refactor items.proto to examples/v1
  - [x] 5.1 Create examples/v1/items.proto with full refactoring
    - Update package to examples.v1
    - Add unique Request/Response messages for each RPC
    - Add FieldMask to UpdateItemRequest
    - Rename price to price_cents, add currency field
    - Add name field following AIP-122 resource naming
    - Import and use common/v1/pagination.proto
    - Import and use common/v1/errors.proto
    - Add protovalidate constraints on all fields
    - Add comprehensive documentation
    - _Requirements: 1.5, 7.1-7.4, 8.1, 10.1, 10.2, 3.1-3.4, 2.1-2.5_
  - [x] 5.2 Write property test for protovalidate validation
    - **Property 2: Protovalidate Validation**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
  - [x] 5.3 Write property test for field mask update semantics
    - **Property 5: Field Mask Update Semantics**
    - **Validates: Requirements 8.1, 8.2, 8.3**
  - [x] 5.4 Write property test for resource name format
    - **Property 7: Resource Name Format**
    - **Validates: Requirements 10.1, 10.2, 10.3**

- [x] 6. Clean up old proto files
  - [x] 6.1 Remove old proto files from non-versioned directories
    - Delete protos/common/errors.proto
    - Delete protos/common/health.proto
    - Delete protos/examples/items.proto
    - Update any imports in generated code
    - _Requirements: 9.1_

- [x] 7. Validate buf lint compliance
  - [x] 7.1 Run buf lint and fix any remaining issues
    - Execute buf lint on all proto files
    - Fix any STANDARD category violations
    - Fix any COMMENTS category violations
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1-2.5_
  - [x] 7.2 Write property test for buf lint compliance
    - **Property 1: Buf Lint Compliance**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1-2.5**
  - [x] 7.3 Write property test for package version suffix
    - **Property 6: Package Version Suffix**
    - **Validates: Requirements 9.1, 9.3**

- [x] 8. Generate Python code
  - [x] 8.1 Run buf generate and verify output
    - Execute buf generate
    - Verify Python files are generated in src/infrastructure/grpc/generated
    - Verify .pyi type stubs are generated
    - Verify protovalidate code is generated
    - _Requirements: 3.5, 6.1, 6.2_

- [x] 9. Update documentation
  - [x] 9.1 Update generated/__init__.py with new exports
    - Export all generated message classes
    - Export all generated service stubs
    - Add module docstring
    - _Requirements: 2.1_
  - [x] 9.2 Create protos/README.md with usage documentation
    - Document proto file structure
    - Document buf commands (lint, generate, breaking)
    - Document validation usage
    - _Requirements: 2.1_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
