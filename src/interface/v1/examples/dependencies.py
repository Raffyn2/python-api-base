"""Dependencies for Examples API routes.

**Feature: example-system-demo**
**Feature: infrastructure-examples-integration-fix**
**Validates: Requirements 2.1, 2.2, 2.3**
"""

from functools import lru_cache
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.examples import (
    ItemExampleResponse,
    ItemExampleUseCase,
    PedidoExampleResponse,
    PedidoExampleUseCase,
)
from core.shared.validation import TypeAdapterCache
from infrastructure.cache.providers import JitterConfig, RedisCacheWithJitter
from infrastructure.db.repositories.examples import (
    ItemExampleRepository,
    PedidoExampleRepository,
)
from infrastructure.db.session import get_async_session
from infrastructure.kafka import EventPublisher, create_event_publisher
from infrastructure.security.rbac import Permission, RBACUser, get_rbac_service


# === TypeAdapter Cache (Singleton Pattern) ===


@lru_cache(maxsize=1)
def get_item_response_adapter() -> TypeAdapterCache[ItemExampleResponse]:
    """Get cached TypeAdapter for ItemExampleResponse."""
    return TypeAdapterCache(ItemExampleResponse)


@lru_cache(maxsize=1)
def get_pedido_response_adapter() -> TypeAdapterCache[PedidoExampleResponse]:
    """Get cached TypeAdapter for PedidoExampleResponse."""
    return TypeAdapterCache(PedidoExampleResponse)


# === Jitter Cache ===

_jitter_cache_instance: RedisCacheWithJitter[dict[str, Any]] | None = None


def get_jitter_cache(request: Request) -> RedisCacheWithJitter[dict[str, Any]] | None:
    """Get RedisCacheWithJitter instance for caching."""
    global _jitter_cache_instance
    redis_client = getattr(request.app.state, "redis", None)

    if redis_client is None:
        return None

    if _jitter_cache_instance is None:
        _jitter_cache_instance = RedisCacheWithJitter[dict[str, Any]](
            redis_client=redis_client,
            config=JitterConfig(
                min_jitter_percent=0.05,
                max_jitter_percent=0.15,
            ),
            key_prefix="examples:",
        )
    return _jitter_cache_instance


# === Repository Dependencies ===


async def get_item_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ItemExampleRepository:
    """Get ItemExampleRepository with injected database session."""
    return ItemExampleRepository(session)


async def get_pedido_repository(
    session: AsyncSession = Depends(get_async_session),
) -> PedidoExampleRepository:
    """Get PedidoExampleRepository with injected database session."""
    return PedidoExampleRepository(session)


def get_event_publisher(request: Request) -> EventPublisher:
    """Get EventPublisher based on Kafka availability."""
    kafka_producer = getattr(request.app.state, "kafka_producer", None)
    return create_event_publisher(kafka_producer)


# === Use Case Dependencies ===


async def get_item_use_case(
    request: Request,
    repo: ItemExampleRepository = Depends(get_item_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ItemExampleUseCase:
    """Get ItemExampleUseCase with real repository and event publisher."""
    cache = get_jitter_cache(request)
    return ItemExampleUseCase(
        repository=repo, kafka_publisher=event_publisher, cache=cache
    )


async def get_pedido_use_case(
    item_repo: ItemExampleRepository = Depends(get_item_repository),
    pedido_repo: PedidoExampleRepository = Depends(get_pedido_repository),
) -> PedidoExampleUseCase:
    """Get PedidoExampleUseCase with real repositories."""
    return PedidoExampleUseCase(
        pedido_repo=pedido_repo,
        item_repo=item_repo,
    )


# === RBAC Dependencies ===


def get_current_user_optional(
    x_user_id: str = Header(default="anonymous", alias="X-User-Id"),
    x_user_roles: str = Header(default="viewer", alias="X-User-Roles"),
) -> RBACUser:
    """Get current user from headers (optional authentication)."""
    roles = [r.strip() for r in x_user_roles.split(",") if r.strip()]
    return RBACUser(id=x_user_id, roles=roles)


def require_write_permission(
    user: RBACUser = Depends(get_current_user_optional),
) -> RBACUser:
    """Require WRITE permission for modifying resources."""
    rbac = get_rbac_service()
    if not rbac.check_permission(user, Permission.WRITE):
        perm = Permission.WRITE.value
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{perm}' required. User roles: {user.roles}",
        )
    return user


def require_delete_permission(
    user: RBACUser = Depends(get_current_user_optional),
) -> RBACUser:
    """Require DELETE permission for deleting resources."""
    rbac = get_rbac_service()
    if not rbac.check_permission(user, Permission.DELETE):
        perm = Permission.DELETE.value
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{perm}' required. User roles: {user.roles}",
        )
    return user
