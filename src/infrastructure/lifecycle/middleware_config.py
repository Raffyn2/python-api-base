"""Middleware configuration module.

**Feature: code-review-2025**
**Refactored from: main.py (604 lines)
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from fastapi.middleware.cors import CORSMiddleware

from core.config import (
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_REQUEST_SIZE_BYTES,
    DELETE_RATE_LIMIT_REQUESTS,
    IMPORT_REQUEST_SIZE_BYTES,
    READ_RATE_LIMIT_REQUESTS,
    UPLOAD_REQUEST_SIZE_BYTES,
    WRITE_RATE_LIMIT_REQUESTS,
    get_settings,
)
from core.shared.logging import get_logger
from infrastructure.audit import InMemoryAuditStore
from infrastructure.idempotency import IdempotencyConfig, IdempotencyMiddleware
from infrastructure.observability import LoggingMiddleware
from infrastructure.prometheus import setup_prometheus
from infrastructure.ratelimit import (
    InMemoryRateLimiter,
    IPClientExtractor,
    RateLimit,
    RateLimitConfig,
    RateLimitMiddleware,
)
from interface.middleware.logging import RequestLoggerMiddleware
from interface.middleware.production import (
    AuditConfig,
    MultitenancyConfig,
    ResilienceConfig,
    setup_production_middleware,
)
from interface.middleware.request import (
    RequestIDMiddleware,
    RequestSizeLimitMiddleware,
)
from interface.middleware.security import SecurityHeadersMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = get_logger(__name__)


def configure_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application.

    Middleware stack order (outermost to innermost):
    1. RequestIDMiddleware - Generate/propagate X-Request-ID
    2. LoggingMiddleware - Correlation ID and structured logging
    3. RequestLoggerMiddleware - Request/response logging with PII masking
    4. CORSMiddleware - Cross-origin resource sharing
    5. SecurityHeadersMiddleware - Security headers (CSP, HSTS, etc.)
    6. RequestSizeLimitMiddleware - Limit request body size
    7. ResilienceMiddleware - Circuit breaker pattern
    8. MultitenancyMiddleware - Tenant context resolution
    9. AuditMiddleware - Request audit trail
    10. RateLimitMiddleware - Rate limiting
    """
    settings = get_settings()

    _configure_request_id_middleware(app)
    _configure_logging_middleware(app, settings)
    _configure_request_logger_middleware(app)
    _configure_cors_middleware(app, settings)
    _configure_security_headers_middleware(app)
    _configure_request_size_middleware(app)
    _configure_production_middleware(app)


def _configure_request_id_middleware(app: FastAPI) -> None:
    """Configure RequestIDMiddleware."""
    app.add_middleware(RequestIDMiddleware)
    logger.info("middleware_configured", middleware="RequestIDMiddleware")


def _configure_logging_middleware(app: FastAPI, settings) -> None:
    """Configure LoggingMiddleware."""
    app.add_middleware(
        LoggingMiddleware,
        service_name=settings.observability.service_name,
        excluded_paths=["/health/live", "/health/ready", "/metrics", "/docs", "/redoc"],
    )
    logger.info("middleware_configured", middleware="LoggingMiddleware")


def _configure_request_logger_middleware(app: FastAPI) -> None:
    """Configure RequestLoggerMiddleware."""
    app.add_middleware(
        RequestLoggerMiddleware,
        log_request_body=False,
        log_response_body=False,
        excluded_paths=[
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
    )
    logger.info("middleware_configured", middleware="RequestLoggerMiddleware")


def _configure_cors_middleware(app: FastAPI, settings) -> None:
    """Configure CORSMiddleware with security validation."""
    if "*" in settings.security.cors_origins:
        error_msg = (
            "CRITICAL SECURITY ERROR: CORS allow_credentials=True requires specific "
            "origins, not wildcard ['*']. This combination allows any origin to send "
            "credentials, enabling CSRF attacks. Set SECURITY__CORS_ORIGINS to specific "
            "domains (e.g., ['https://app.example.com', 'https://admin.example.com'])"
        )
        logger.error("cors_security_violation", error=error_msg)
        raise ValueError(error_msg)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _configure_security_headers_middleware(app: FastAPI) -> None:
    """Configure SecurityHeadersMiddleware."""
    app.add_middleware(
        SecurityHeadersMiddleware,
        content_security_policy=(
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        x_frame_options="DENY",
        x_content_type_options="nosniff",
        x_xss_protection="1; mode=block",
        strict_transport_security="max-age=31536000; includeSubDomains; preload",
        referrer_policy="strict-origin-when-cross-origin",
        permissions_policy=(
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()"
        ),
    )
    logger.info("middleware_configured", middleware="SecurityHeadersMiddleware")


def _configure_request_size_middleware(app: FastAPI) -> None:
    """Configure RequestSizeLimitMiddleware."""
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=DEFAULT_REQUEST_SIZE_BYTES,
        route_limits={
            r"^/api/v1/upload.*": UPLOAD_REQUEST_SIZE_BYTES,
            r"^/api/v1/import.*": IMPORT_REQUEST_SIZE_BYTES,
        },
    )
    logger.info(
        "middleware_configured",
        middleware="RequestSizeLimitMiddleware",
        max_size="10MB",
    )


def _configure_production_middleware(app: FastAPI) -> None:
    """Configure production middleware stack."""
    setup_production_middleware(
        app,
        resilience_config=ResilienceConfig(
            failure_threshold=5,
            timeout=timedelta(seconds=30.0),
            enabled=True,
        ),
        multitenancy_config=MultitenancyConfig(
            required=False,
            header_name="X-Tenant-ID",
        ),
        audit_store=InMemoryAuditStore(),
        audit_config=AuditConfig(
            enabled=True,
            exclude_paths={"/health", "/metrics", "/docs", "/redoc", "/openapi.json"},
        ),
    )


def configure_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting middleware."""
    config = RateLimitConfig(
        default_limit=RateLimit(
            requests=DEFAULT_RATE_LIMIT_REQUESTS,
            window=timedelta(minutes=1),
        ),
    )
    limiter = InMemoryRateLimiter[str](config)

    limiter.configure(
        {
            "GET:/api/v1/examples/*": RateLimit(
                requests=READ_RATE_LIMIT_REQUESTS,
                window=timedelta(minutes=1),
            ),
            "POST:/api/v1/examples/*": RateLimit(
                requests=WRITE_RATE_LIMIT_REQUESTS,
                window=timedelta(minutes=1),
            ),
            "PUT:/api/v1/examples/*": RateLimit(
                requests=WRITE_RATE_LIMIT_REQUESTS,
                window=timedelta(minutes=1),
            ),
            "DELETE:/api/v1/examples/*": RateLimit(
                requests=DELETE_RATE_LIMIT_REQUESTS,
                window=timedelta(minutes=1),
            ),
        }
    )

    app.add_middleware(
        RateLimitMiddleware[str],
        limiter=limiter,
        extractor=IPClientExtractor(),
        exclude_paths={
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        },
    )

    logger.info(
        "rate_limiting_configured",
        default_limit=f"{DEFAULT_RATE_LIMIT_REQUESTS}/min",
    )


def configure_idempotency(app: FastAPI) -> None:
    """Configure idempotency middleware for POST/PUT operations."""
    app.add_middleware(
        IdempotencyMiddleware,
        handler=None,
        methods={"POST", "PUT"},
        required_endpoints={
            "/api/v1/examples/items",
            "/api/v1/examples/pedidos",
        },
        exclude_paths={"/health", "/metrics", "/docs", "/redoc"},
        config=IdempotencyConfig(
            ttl_hours=24,
            key_prefix="api:idempotency",
        ),
    )
    logger.info(
        "idempotency_middleware_configured",
        endpoints=["/api/v1/examples/items", "/api/v1/examples/pedidos"],
    )


def configure_prometheus(app: FastAPI) -> None:
    """Configure Prometheus metrics if enabled."""
    settings = get_settings()
    obs = settings.observability

    if obs.prometheus_enabled:
        setup_prometheus(
            app,
            endpoint=obs.prometheus_endpoint,
            include_in_schema=obs.prometheus_include_in_schema,
            skip_paths=["/health/live", "/health/ready", "/docs", "/redoc"],
        )
        logger.info(
            "prometheus_configured",
            endpoint=obs.prometheus_endpoint,
            namespace=obs.prometheus_namespace,
        )
    else:
        logger.info("prometheus_disabled", reason="prometheus_enabled=false")
