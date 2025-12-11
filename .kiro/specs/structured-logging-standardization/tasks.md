# Implementation Plan

- [x] 1. Create StructuredLogEntry data model and formatter
  - [x] 1.1 Create `src/core/structured_logging/structured.py` with StructuredLogEntry dataclass
    - Implement frozen dataclass with message, level, timestamp, extra fields
    - Add `__post_init__` validation for required `operation` field
    - _Requirements: 1.4, 8.1_
  - [x] 1.2 Implement JSONLogFormatter class with format/parse methods
    - Implement `format()` to serialize entry to JSON string
    - Implement `parse()` to deserialize JSON string back to entry
    - Handle serialization errors gracefully
    - _Requirements: 8.1, 8.2_
  - [x] 1.3 Write property test for log entry round-trip
    - **Property 2: Log Entry Round-Trip Consistency**
    - **Validates: Requirements 8.1, 8.2, 8.3**
  - [x] 1.4 Write property test for operation field presence
    - **Property 1: Operation Field Presence**
    - **Validates: Requirements 1.4**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Refactor Infrastructure Layer - Redis modules
  - [x] 3.1 Convert logging in `src/infrastructure/redis/operations.py`
    - Replace f-strings with structured logging using extra={}
    - Add operation tags (REDIS_GET, REDIS_SET, REDIS_DELETE, etc.)
    - _Requirements: 4.1_
  - [x] 3.2 Convert logging in `src/infrastructure/redis/connection.py`
    - Replace f-strings with structured logging
    - Add operation tags (REDIS_CONNECT, REDIS_DISCONNECT)
    - _Requirements: 4.1_
  - [x] 3.3 Convert logging in `src/infrastructure/redis/invalidation.py`
    - Replace f-strings with structured logging
    - Add operation tags (REDIS_INVALIDATE)
    - _Requirements: 4.1_

- [x] 4. Refactor Infrastructure Layer - Kafka modules
  - [x] 4.1 Convert logging in `src/infrastructure/kafka/consumer.py`
    - Replace f-strings with structured logging
    - Add operation tags (KAFKA_CONSUME, KAFKA_COMMIT, KAFKA_ERROR)
    - _Requirements: 4.1_
  - [x] 4.2 Convert logging in `src/infrastructure/kafka/event_publisher.py`
    - Replace f-strings with structured logging
    - Add operation tags (KAFKA_PUBLISH)
    - _Requirements: 4.1_

- [x] 5. Refactor Infrastructure Layer - Cache providers
  - [x] 5.1 Convert logging in `src/infrastructure/cache/providers/redis_jitter.py`
    - Replace f-strings with structured logging
    - Add operation tags (CACHE_GET, CACHE_SET, CACHE_JITTER)
    - _Requirements: 4.2_
  - [x] 5.2 Convert logging in `src/infrastructure/cache/providers/redis.py`
  - [x] 5.3 Convert logging in `src/infrastructure/cache/providers/redis_cache.py`

- [x] 6. Refactor Infrastructure Layer - Database modules
  - [x] 6.1 Convert logging in `src/infrastructure/scylladb/client.py`
    - Replace f-strings with structured logging
    - Add operation tags (SCYLLA_CONNECT, SCYLLA_QUERY)
    - _Requirements: 4.1_
  - [ ] 6.2 Convert logging in `src/infrastructure/scylladb/repository.py` (NOT FOUND)
  - [ ] 6.3 Convert logging in `src/infrastructure/db/repositories/item_example.py` (NO LOGGING)
  - [ ] 6.4 Convert logging in `src/infrastructure/db/repositories/pedido_example.py` (NO LOGGING)

- [x] 7. Refactor Infrastructure Layer - Messaging modules
  - [x] 7.1 Convert logging in `src/infrastructure/idempotency/middleware.py`
    - Replace f-strings with structured logging
    - Add operation tags (IDEMPOTENCY_CHECK, IDEMPOTENCY_STORE)
    - _Requirements: 4.3_
  - [x] 7.2 Convert logging in `src/infrastructure/idempotency/handler.py`
    - Replace f-strings with structured logging
    - Add operation tags (IDEMPOTENCY_HANDLE)
    - _Requirements: 4.3_

- [x] 8. Refactor Infrastructure Layer - Observability modules
  - [x] 8.1 Convert logging in `src/infrastructure/observability/tracing.py`
    - Replace f-strings with structured logging
    - Add operation tags (TRACE_START, TRACE_END)
    - _Requirements: 4.4_
  - [x] 8.2 Convert logging in `src/infrastructure/observability/metrics.py`
    - Replace f-strings with structured logging
    - Add operation tags (METRICS_RECORD)
    - _Requirements: 4.4_
  - [x] 8.3 Convert logging in `src/infrastructure/observability/telemetry/service.py`
    - Replace f-strings with structured logging
    - Add operation tags (TELEMETRY_*)
    - _Requirements: 4.4_
  - [x] 8.4 Convert logging in `src/infrastructure/observability/elasticsearch_buffer.py`
    - Replace f-strings with structured logging
    - Add operation tags (ES_BUFFER_*)
    - _Requirements: 4.4_

- [x] 9. Refactor Infrastructure Layer - Security and other modules
  - [x] 9.1 Convert logging in `src/infrastructure/security/rbac.py`
    - Replace f-strings with structured logging
    - Add operation tags (RBAC_CHECK, RBAC_DENY)
    - _Requirements: 4.1_
  - [x] 9.2 Convert logging in `src/infrastructure/sustainability/client.py`
    - Replace f-strings with structured logging
    - Add operation tags (SUSTAINABILITY_*)
    - _Requirements: 4.1_
  - [x] 9.3 Convert logging in `src/infrastructure/tasks/rabbitmq/queue.py`
    - Replace f-strings with structured logging
    - Add operation tags (RABBITMQ_QUEUE_*)
    - _Requirements: 4.1_
  - [x] 9.4 Convert logging in `src/infrastructure/tasks/rabbitmq/worker.py`
    - Replace f-strings with structured logging
    - Add operation tags (RABBITMQ_WORKER_*)
    - _Requirements: 4.1_
  - [x] 9.5 Convert logging in `src/infrastructure/rbac/audit.py`
    - Replace f-strings with structured logging
    - Add operation tags (AUDIT_*)
    - _Requirements: 4.1_

- [x] 10. Checkpoint - Verify Infrastructure Layer
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Refactor Application Layer - Services
  - [x] 11.1 Convert logging in `src/application/common/services/generic_service.py` (uses % formatting - OK)
  - [ ] 11.2 Convert logging in `src/application/common/services/cache/cache_service.py` (NOT FOUND)

- [x] 12. Refactor Application Layer - Use Cases
  - [x] 12.1 Convert logging in `src/application/common/use_cases/base_use_case.py`
    - Replace f-strings with structured logging
    - Add operation tags (USE_CASE_*)
    - _Requirements: 5.2_
  - [ ] 12.2 Convert logging in `src/application/examples/order/use_cases/place_order.py` (NOT FOUND)

- [x] 13. Checkpoint - Verify Application Layer
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Refactor Interface Layer - Routers
  - [x] 14.1 Convert logging in `src/interface/v1/core/health_router.py`
    - Replace f-strings with structured logging
    - Add operation tags (HEALTH_CHECK)
    - _Requirements: 6.1_
  - [ ] 14.2 Convert logging in `src/interface/v1/features/kafka_router.py` (NO F-STRING LOGGING)

- [x] 15. Refactor Interface Layer - Middleware
  - [x] 15.1 Convert logging in `src/interface/middleware/middleware_chain.py`
    - Replace f-strings with structured logging
    - Add operation tags (MIDDLEWARE_*)
    - _Requirements: 6.1_
  - [x] 15.2 Convert logging in `src/interface/middleware/production/audit.py`
    - Replace f-strings with structured logging
    - Add operation tags (AUDIT_*)
    - _Requirements: 6.2_
  - [x] 15.3 Convert logging in `src/interface/middleware/production/multitenancy.py`
    - Replace f-strings with structured logging
    - Add operation tags (TENANT_*)
    - _Requirements: 6.2_
  - [x] 15.4 Convert logging in `src/interface/middleware/production/resilience.py`
    - Replace f-strings with structured logging
    - Add operation tags (RESILIENCE_*)
    - _Requirements: 6.2_

- [x] 16. Refactor Scripts
  - [x] 16.1 Convert logging in `scripts/seed_examples.py`
    - Replace f-strings with structured logging
    - Add operation tags (SEED_*)
    - _Requirements: 6.1_

- [x] 17. Final Checkpoint - Run full linter verification
  - All 68 G004 violations fixed
  - Run `ruff check --select=G004 src/` - All checks passed!
  - All 12 property-based tests passing
