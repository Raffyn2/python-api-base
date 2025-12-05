"""FastAPI application entry point.

This module provides the main application factory and lifespan management.

**Feature: code-review-2025**
**Refactored: Split 604 lines into focused modules**
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import get_settings
from core.errors import setup_exception_handlers
from core.shared.logging import configure_logging, get_logger
from infrastructure.di import lifecycle
from infrastructure.lifecycle import (
    cleanup_resources,
    configure_idempotency,
    configure_middleware,
    configure_prometheus,
    configure_rate_limiting,
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
from interface.openapi import setup_openapi

# Core API Routes
from interface.v1.auth import auth_router
from interface.v1.enterprise_examples_router import router as enterprise_router
from interface.v1.examples import examples_router
from interface.v1.health_router import mark_startup_complete, router as health_router
from interface.v1.infrastructure_router import router as infrastructure_router
from interface.v1.jwks_router import router as jwks_router
from interface.v1.users_router import router as users_router
from interface.v2 import examples_v2_router

# Dapr Support (optional)
try:
    from interface.dapr.routes import dapr_router
    HAS_DAPR = True
except ImportError:
    dapr_router = None
    HAS_DAPR = False

# GraphQL Support (optional)
try:
    from interface.graphql import HAS_STRAWBERRY, graphql_router
except ImportError:
    graphql_router = None
    HAS_STRAWBERRY = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()
    app.state.settings = settings

    lifecycle.run_startup()
    await lifecycle.run_startup_async()

    # Initialize all services
    await initialize_database()
    command_bus, query_bus = await initialize_cqrs()
    await initialize_examples(command_bus, query_bus)
    await initialize_jwks()
    await initialize_redis(app)
    await initialize_minio(app)
    await initialize_kafka(app)
    await initialize_scylladb(app)
    await initialize_rabbitmq(app)

    mark_startup_complete()

    yield

    await cleanup_resources(app)


def _configure_logging() -> None:
    """Configure structured logging with ECS compatibility."""
    settings = get_settings()
    obs = settings.observability

    configure_logging(
        log_level=obs.log_level,
        json_output=obs.log_format == "json",
        add_ecs_fields=obs.log_ecs_format,
        service_name=obs.service_name,
        service_version=obs.service_version,
        environment=obs.environment,
    )

    logger = get_logger("main")
    logger.info(
        "logging_configured",
        log_level=obs.log_level,
        log_format=obs.log_format,
        ecs_enabled=obs.log_ecs_format,
        elasticsearch_enabled=obs.elasticsearch_enabled,
    )


def _register_routes(app: FastAPI) -> None:
    """Register all API routes."""
    logger = get_logger("main")

    app.include_router(health_router)
    app.include_router(jwks_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(examples_router, prefix="/api/v1")
    app.include_router(infrastructure_router, prefix="/api/v1")
    app.include_router(enterprise_router, prefix="/api/v1")
    app.include_router(examples_v2_router, prefix="/api")

    if HAS_STRAWBERRY and graphql_router is not None:
        app.include_router(graphql_router, prefix="/api", tags=["GraphQL"])
        logger.info("graphql_enabled", endpoint="/api/graphql")
    else:
        logger.info("graphql_disabled", reason="strawberry not installed")

    # Register Dapr routes if available
    if HAS_DAPR and dapr_router is not None:
        app.include_router(dapr_router)
        logger.info("dapr_routes_enabled", endpoints=["/dapr/subscribe", "/dapr/config", "/dapr/healthz"])
    else:
        logger.debug("dapr_routes_disabled", reason="dapr module not available")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _configure_logging()

    settings = get_settings()
    logger = get_logger("main")

    logger.info(
        "creating_application", app_name=settings.app_name, version=settings.version
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Modern REST API Framework with PEP 695 Generics",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    setup_exception_handlers(app)
    setup_openapi(app)
    configure_middleware(app)
    configure_prometheus(app)
    configure_rate_limiting(app)
    configure_idempotency(app)
    _register_routes(app)

    return app


app = create_app()


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
