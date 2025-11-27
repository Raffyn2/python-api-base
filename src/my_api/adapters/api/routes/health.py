"""Health check routes."""

from enum import Enum
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter(tags=["Health"])


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    """Health status for a single dependency."""

    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: HealthStatus
    checks: dict[str, DependencyHealth]
    version: str | None = None


async def check_database(request: Request) -> DependencyHealth:
    """Check database connectivity.
    
    Args:
        request: FastAPI request with app state.
        
    Returns:
        Database health status.
    """
    import time
    
    try:
        db = getattr(request.app.state, "db", None)
        if db is None:
            return DependencyHealth(
                status=HealthStatus.UNHEALTHY,
                message="Database not initialized",
            )
        
        start = time.perf_counter()
        async with db.session() as session:
            await session.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        
        return DependencyHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return DependencyHealth(
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


async def check_redis(request: Request) -> DependencyHealth:
    """Check Redis connectivity (optional).
    
    Args:
        request: FastAPI request with app state.
        
    Returns:
        Redis health status.
    """
    import time
    
    try:
        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            return DependencyHealth(
                status=HealthStatus.HEALTHY,
                message="Redis not configured (optional)",
            )
        
        start = time.perf_counter()
        await redis.ping()
        latency = (time.perf_counter() - start) * 1000
        
        return DependencyHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return DependencyHealth(
            status=HealthStatus.DEGRADED,
            message=f"Redis unavailable: {e}",
        )


@router.get("/health/live", summary="Liveness check")
async def liveness() -> dict[str, str]:
    """Check if the service is alive.
    
    This endpoint is used by Kubernetes liveness probes.
    It should return 200 if the service is running.
    """
    return {"status": "ok"}


@router.get(
    "/health/ready",
    summary="Readiness check",
    response_model=HealthResponse,
)
async def readiness(request: Request, response: Response) -> HealthResponse:
    """Check if the service is ready to accept requests.
    
    This endpoint checks all dependencies and returns detailed status.
    Used by Kubernetes readiness probes.
    """
    checks: dict[str, DependencyHealth] = {}
    
    # Check database
    checks["database"] = await check_database(request)
    
    # Check Redis (optional)
    checks["redis"] = await check_redis(request)
    
    # Determine overall status
    statuses = [check.status for check in checks.values()]
    
    if HealthStatus.UNHEALTHY in statuses:
        overall_status = HealthStatus.UNHEALTHY
        response.status_code = 503
    elif HealthStatus.DEGRADED in statuses:
        overall_status = HealthStatus.DEGRADED
        response.status_code = 200  # Still accepting requests
    else:
        overall_status = HealthStatus.HEALTHY
    
    # Get version from settings
    settings = getattr(request.app.state, "settings", None)
    version = settings.version if settings else None
    
    return HealthResponse(
        status=overall_status,
        checks=checks,
        version=version,
    )
