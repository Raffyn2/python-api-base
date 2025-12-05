"""gRPC health check service implementation.

This module provides a health check service that follows the
standard gRPC health checking protocol.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from enum import Enum
from typing import Any

from structlog import get_logger

logger = get_logger(__name__)


class ServingStatus(Enum):
    """Health check serving status."""
    UNKNOWN = 0
    SERVING = 1
    NOT_SERVING = 2
    SERVICE_UNKNOWN = 3


class HealthServicer:
    """gRPC health check service implementation.
    
    Implements the standard gRPC health checking protocol with
    support for dependency checks.
    """

    def __init__(
        self,
        dependency_checks: dict[str, Callable[[], Awaitable[bool]]] | None = None,
        check_interval: float = 5.0,
    ) -> None:
        """Initialize health servicer.
        
        Args:
            dependency_checks: Dict of service name to health check function
            check_interval: Interval for Watch streaming in seconds
        """
        self._dependency_checks = dependency_checks or {}
        self._check_interval = check_interval
        self._service_status: dict[str, ServingStatus] = {}
        self._is_shutting_down = False

    def set_serving(self, service: str = "") -> None:
        """Set a service as serving.
        
        Args:
            service: Service name (empty for overall health)
        """
        self._service_status[service] = ServingStatus.SERVING
        logger.info("health_status_changed", service=service, status="SERVING")

    def set_not_serving(self, service: str = "") -> None:
        """Set a service as not serving.
        
        Args:
            service: Service name (empty for overall health)
        """
        self._service_status[service] = ServingStatus.NOT_SERVING
        logger.info("health_status_changed", service=service, status="NOT_SERVING")

    def enter_graceful_shutdown(self) -> None:
        """Enter graceful shutdown mode.
        
        Sets all services to NOT_SERVING.
        """
        self._is_shutting_down = True
        for service in list(self._service_status.keys()):
            self._service_status[service] = ServingStatus.NOT_SERVING
        self._service_status[""] = ServingStatus.NOT_SERVING
        logger.info("health_graceful_shutdown")

    async def check(self, service: str = "") -> ServingStatus:
        """Check health status of a service.
        
        Args:
            service: Service name to check (empty for overall)
            
        Returns:
            The serving status
        """
        if self._is_shutting_down:
            return ServingStatus.NOT_SERVING

        # Check if service is known
        if service and service not in self._service_status and service not in self._dependency_checks:
            return ServingStatus.SERVICE_UNKNOWN

        # Run dependency checks for the service
        if service in self._dependency_checks:
            try:
                is_healthy = await self._dependency_checks[service]()
                return ServingStatus.SERVING if is_healthy else ServingStatus.NOT_SERVING
            except Exception as exc:
                logger.error(
                    "health_check_failed",
                    service=service,
                    error=str(exc),
                )
                return ServingStatus.NOT_SERVING

        # Check overall health (all dependencies)
        if not service:
            return await self._check_all_dependencies()

        # Return cached status
        return self._service_status.get(service, ServingStatus.UNKNOWN)

    async def _check_all_dependencies(self) -> ServingStatus:
        """Check all dependencies for overall health.
        
        Returns:
            SERVING if all dependencies are healthy
        """
        if not self._dependency_checks:
            return self._service_status.get("", ServingStatus.SERVING)

        for name, check_func in self._dependency_checks.items():
            try:
                is_healthy = await check_func()
                if not is_healthy:
                    logger.warning(
                        "health_dependency_unhealthy",
                        dependency=name,
                    )
                    return ServingStatus.NOT_SERVING
            except Exception as exc:
                logger.error(
                    "health_dependency_check_failed",
                    dependency=name,
                    error=str(exc),
                )
                return ServingStatus.NOT_SERVING

        return ServingStatus.SERVING

    async def watch(self, service: str = "") -> AsyncIterator[ServingStatus]:
        """Stream health status updates.
        
        Args:
            service: Service name to watch
            
        Yields:
            Status updates when health changes
        """
        last_status: ServingStatus | None = None
        
        while not self._is_shutting_down:
            current_status = await self.check(service)
            
            if current_status != last_status:
                last_status = current_status
                yield current_status
            
            await asyncio.sleep(self._check_interval)
        
        # Final status on shutdown
        yield ServingStatus.NOT_SERVING


# gRPC servicer adapter for grpc_health.v1
class GRPCHealthServicer:
    """Adapter for grpc_health.v1.HealthServicer."""

    def __init__(self, health_servicer: HealthServicer) -> None:
        """Initialize adapter.
        
        Args:
            health_servicer: The health servicer instance
        """
        self._health = health_servicer

    async def Check(
        self,
        request: Any,
        context: Any,
    ) -> Any:
        """Handle Check RPC.
        
        Args:
            request: HealthCheckRequest
            context: ServicerContext
            
        Returns:
            HealthCheckResponse
        """
        try:
            from grpc_health.v1 import health_pb2
            
            service = request.service
            status = await self._health.check(service)
            
            return health_pb2.HealthCheckResponse(
                status=status.value,
            )
        except ImportError:
            # Return a simple response if grpc_health not available
            status = await self._health.check(request.service if hasattr(request, "service") else "")
            return {"status": status.value}

    async def Watch(
        self,
        request: Any,
        context: Any,
    ) -> AsyncIterator[Any]:
        """Handle Watch RPC.
        
        Args:
            request: HealthCheckRequest
            context: ServicerContext
            
        Yields:
            HealthCheckResponse updates
        """
        try:
            from grpc_health.v1 import health_pb2
            
            service = request.service
            async for status in self._health.watch(service):
                yield health_pb2.HealthCheckResponse(
                    status=status.value,
                )
        except ImportError:
            async for status in self._health.watch(request.service if hasattr(request, "service") else ""):
                yield {"status": status.value}
