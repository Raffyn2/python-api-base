"""Dapr route registration.

This module registers all Dapr endpoints with FastAPI.
"""

from typing import Any

from fastapi import APIRouter, Request, Response

from core.shared.logging import get_logger
from infrastructure.dapr.health import HealthChecker, HealthStatus

logger = get_logger(__name__)

dapr_router = APIRouter(prefix="/dapr", tags=["Dapr"])


@dapr_router.get("/subscribe")
async def get_subscriptions() -> list[dict[str, Any]]:
    """Return list of pub/sub subscriptions for Dapr.

    This endpoint is called by Dapr to discover subscriptions.
    """
    from infrastructure.dapr.client import get_dapr_client

    try:
        client = get_dapr_client()
        if hasattr(client, "_pubsub_manager") and client._pubsub_manager:
            return client._pubsub_manager.get_subscriptions()
    except Exception:
        pass

    return []


@dapr_router.get("/config")
async def get_dapr_config() -> dict[str, Any]:
    """Return Dapr actor configuration.

    This endpoint is called by Dapr to discover actor types.
    """
    from infrastructure.dapr.actors import ActorRuntime

    runtime = ActorRuntime()
    return runtime.get_actor_config()


@dapr_router.get("/healthz")
async def dapr_health_check() -> Response:
    """Dapr health check endpoint.

    Returns 204 if healthy, 503 if unhealthy.
    """
    from core.config.dapr import get_dapr_settings

    settings = get_dapr_settings()
    checker = HealthChecker(settings.http_endpoint)
    status = await checker.check_sidecar_health()

    if status == HealthStatus.HEALTHY:
        return Response(status_code=204)
    return Response(status_code=503)


@dapr_router.get("/health")
async def dapr_health_details() -> dict[str, Any]:
    """Get detailed Dapr health information."""
    from core.config.dapr import get_dapr_settings

    settings = get_dapr_settings()
    checker = HealthChecker(settings.http_endpoint)
    health = await checker.get_full_health()

    return {
        "sidecar_status": health.sidecar_status.value,
        "version": health.version,
        "components": [
            {
                "name": c.name,
                "type": c.type,
                "status": c.status.value,
                "message": c.message,
            }
            for c in health.components
        ],
    }


@dapr_router.post("/subscribe/{pubsub}/{topic}")
async def handle_subscription(
    pubsub: str,
    topic: str,
    request: Request,
) -> dict[str, str]:
    """Handle incoming pub/sub messages.

    Args:
        pubsub: Pub/sub component name.
        topic: Topic name.
        request: Incoming request.

    Returns:
        Status response for Dapr.
    """
    from infrastructure.dapr.pubsub import CloudEvent, MessageStatus

    try:
        body = await request.json()
        event = CloudEvent(**body)

        from infrastructure.dapr.client import get_dapr_client

        client = get_dapr_client()
        if hasattr(client, "_pubsub_manager") and client._pubsub_manager:
            status = await client._pubsub_manager.handle_message(pubsub, topic, event)
            return {"status": status.value}

        return {"status": MessageStatus.DROP.value}
    except Exception as e:
        logger.error(
            "subscription_handler_error",
            pubsub=pubsub,
            topic=topic,
            error=str(e),
        )
        return {"status": "RETRY"}


@dapr_router.post("/bindings/{binding_name}")
async def handle_binding(
    binding_name: str,
    request: Request,
) -> dict[str, Any] | None:
    """Handle incoming binding events.

    Args:
        binding_name: Binding component name.
        request: Incoming request.

    Returns:
        Optional response data.
    """
    try:
        body = await request.json()
        metadata = dict(request.headers)

        from infrastructure.dapr.client import get_dapr_client

        client = get_dapr_client()
        if hasattr(client, "_bindings_manager") and client._bindings_manager:
            return await client._bindings_manager.handle_event(
                binding_name, body, metadata
            )

        return None
    except Exception as e:
        logger.error(
            "binding_handler_error",
            binding=binding_name,
            error=str(e),
        )
        raise


@dapr_router.api_route(
    "/actors/{actor_type}/{actor_id}/method/{method_name}",
    methods=["GET", "POST", "PUT", "DELETE"],
)
async def handle_actor_method(
    actor_type: str,
    actor_id: str,
    method_name: str,
    request: Request,
) -> Any:
    """Handle actor method invocation.

    Args:
        actor_type: Actor type name.
        actor_id: Actor instance ID.
        method_name: Method name to invoke.
        request: Incoming request.

    Returns:
        Method result.
    """
    logger.debug(
        "actor_method_invoked",
        actor_type=actor_type,
        actor_id=actor_id,
        method=method_name,
    )

    raise NotImplementedError("Actor method invocation requires DaprActor extension")


@dapr_router.put("/actors/{actor_type}/{actor_id}/method/remind/{reminder_name}")
async def handle_actor_reminder(
    actor_type: str,
    actor_id: str,
    reminder_name: str,
    request: Request,
) -> None:
    """Handle actor reminder callback.

    Args:
        actor_type: Actor type name.
        actor_id: Actor instance ID.
        reminder_name: Reminder name.
        request: Incoming request.
    """
    logger.debug(
        "actor_reminder_triggered",
        actor_type=actor_type,
        actor_id=actor_id,
        reminder=reminder_name,
    )

    raise NotImplementedError("Actor reminders require DaprActor extension")


@dapr_router.put("/actors/{actor_type}/{actor_id}/method/timer/{timer_name}")
async def handle_actor_timer(
    actor_type: str,
    actor_id: str,
    timer_name: str,
    request: Request,
) -> None:
    """Handle actor timer callback.

    Args:
        actor_type: Actor type name.
        actor_id: Actor instance ID.
        timer_name: Timer name.
        request: Incoming request.
    """
    logger.debug(
        "actor_timer_triggered",
        actor_type=actor_type,
        actor_id=actor_id,
        timer=timer_name,
    )

    raise NotImplementedError("Actor timers require DaprActor extension")
