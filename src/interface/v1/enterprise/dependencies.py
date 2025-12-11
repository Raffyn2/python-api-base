"""Enterprise examples dependencies.

**Feature: enterprise-generics-2025**
"""

from datetime import timedelta

import structlog

from infrastructure.ratelimit import InMemoryRateLimiter, RateLimit, RateLimitConfig
from infrastructure.rbac import (
    RBAC,
    AuditLogger,
    InMemoryAuditSink,
    Permission,
    RoleRegistry,
)
from infrastructure.tasks import RabbitMQConfig, RabbitMQTaskQueue
from interface.v1.enterprise.models import (
    EmailTaskPayload,
    ExampleAction,
    ExampleResource,
    ExampleUser,
)

logger = structlog.get_logger(__name__)

# Singletons (initialized on first use)
_rate_limiter: InMemoryRateLimiter[str] | None = None
_role_registry: RoleRegistry[ExampleResource, ExampleAction] | None = None
_rbac: RBAC[ExampleUser, ExampleResource, ExampleAction] | None = None
_task_queue: RabbitMQTaskQueue[EmailTaskPayload, str] | None = None
_audit_logger: AuditLogger[ExampleUser, ExampleResource, ExampleAction] | None = None


def get_rate_limiter() -> InMemoryRateLimiter[str]:
    """Get or create rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        config = RateLimitConfig(default_limit=RateLimit(requests=10, window=timedelta(minutes=1)))
        _rate_limiter = InMemoryRateLimiter[str](config)
        logger.info("rate_limiter_initialized", default_limit="10/min")
    return _rate_limiter


def get_role_registry() -> RoleRegistry[ExampleResource, ExampleAction]:
    """Get or create role registry."""
    global _role_registry
    if _role_registry is None:
        _role_registry = RoleRegistry[ExampleResource, ExampleAction]()

        _role_registry.create_role(
            name="viewer",
            permissions={
                Permission(ExampleResource.DOCUMENT, ExampleAction.READ),
                Permission(ExampleResource.DOCUMENT, ExampleAction.LIST),
                Permission(ExampleResource.REPORT, ExampleAction.READ),
            },
            description="Read-only access",
        )

        _role_registry.create_role(
            name="editor",
            permissions={
                Permission(ExampleResource.DOCUMENT, ExampleAction.CREATE),
                Permission(ExampleResource.DOCUMENT, ExampleAction.UPDATE),
            },
            description="Edit access",
            parent="viewer",
        )

        _role_registry.create_role(
            name="admin",
            permissions={
                Permission(ExampleResource.DOCUMENT, ExampleAction.DELETE),
                Permission(ExampleResource.USER, ExampleAction.CREATE),
                Permission(ExampleResource.USER, ExampleAction.DELETE),
            },
            description="Full access",
            parent="editor",
        )

        logger.info("role_registry_initialized", roles=["viewer", "editor", "admin"])

    return _role_registry


def get_rbac() -> RBAC[ExampleUser, ExampleResource, ExampleAction]:
    """Get or create RBAC checker."""
    global _rbac
    if _rbac is None:
        _rbac = RBAC[ExampleUser, ExampleResource, ExampleAction](get_role_registry())
    return _rbac


def get_audit_logger() -> AuditLogger[ExampleUser, ExampleResource, ExampleAction]:
    """Get or create audit logger."""
    global _audit_logger
    if _audit_logger is None:
        sink = InMemoryAuditSink()
        _audit_logger = AuditLogger[ExampleUser, ExampleResource, ExampleAction](sink=sink)
    return _audit_logger


async def get_task_queue() -> RabbitMQTaskQueue[EmailTaskPayload, str]:
    """Get or create task queue."""
    global _task_queue
    if _task_queue is None:
        import os

        config = RabbitMQConfig(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            queue_name=os.getenv("RABBITMQ_QUEUE_NAME", "email_tasks"),
        )
        _task_queue = RabbitMQTaskQueue[EmailTaskPayload, str](
            config=config,
            task_type=EmailTaskPayload,
        )
        try:
            await _task_queue.connect()
            logger.info(
                "task_queue_connected",
                host=config.host,
                queue=config.queue_name,
            )
        except Exception:
            logger.exception(
                "task_queue_connection_failed",
                host=config.host,
            )
            raise
    return _task_queue
