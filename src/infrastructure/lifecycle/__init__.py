"""Application lifecycle management.

Provides graceful shutdown handling and lifecycle hooks.

**Feature: code-review-2025**
**Refactored: Extracted startup and middleware config from main.py**
"""

from infrastructure.lifecycle.middleware_config import (
    configure_idempotency,
    configure_middleware,
    configure_prometheus,
    configure_rate_limiting,
)
from infrastructure.lifecycle.shutdown import (
    ShutdownConfig,
    ShutdownHandler,
    ShutdownMiddleware,
    ShutdownState,
    create_shutdown_handler,
    graceful_shutdown_lifespan,
)
from infrastructure.lifecycle.startup import (
    cleanup_resources,
    initialize_cqrs,
    initialize_database,
    initialize_examples,
    initialize_jwks,
    initialize_kafka,
    initialize_minio,
    initialize_rabbitmq,
    initialize_redis,
    initialize_scylladb,
)

__all__ = [
    # Middleware config
    "configure_idempotency",
    "configure_middleware",
    "configure_prometheus",
    "configure_rate_limiting",
    # Shutdown
    "ShutdownConfig",
    "ShutdownHandler",
    "ShutdownMiddleware",
    "ShutdownState",
    "create_shutdown_handler",
    "graceful_shutdown_lifespan",
    # Startup
    "cleanup_resources",
    "initialize_cqrs",
    "initialize_database",
    "initialize_examples",
    "initialize_jwks",
    "initialize_kafka",
    "initialize_minio",
    "initialize_rabbitmq",
    "initialize_redis",
    "initialize_scylladb",
]
