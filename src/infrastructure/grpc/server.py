"""gRPC server implementation with interceptor support.

This module provides an async gRPC server that integrates with the
existing Clean Architecture infrastructure.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from grpc import aio
from structlog import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

logger = get_logger(__name__)


class GRPCServer:
    """Async gRPC server with interceptor and health check support.

    This server integrates with the existing infrastructure including
    observability, authentication, and resilience patterns.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 50051,
        interceptors: Sequence[aio.ServerInterceptor] | None = None,
        max_workers: int = 10,
        max_concurrent_rpcs: int = 100,
        max_message_size: int = 4 * 1024 * 1024,
        reflection_enabled: bool = True,
        health_check_enabled: bool = True,
    ) -> None:
        """Initialize gRPC server.

        Args:
            host: Server host address
            port: Server port
            interceptors: List of server interceptors
            max_workers: Maximum worker threads
            max_concurrent_rpcs: Maximum concurrent RPCs
            max_message_size: Maximum message size in bytes
            reflection_enabled: Enable gRPC reflection
            health_check_enabled: Enable health check service
        """
        self._host = host
        self._port = port
        self._interceptors = list(interceptors) if interceptors else []
        self._max_workers = max_workers
        self._max_concurrent_rpcs = max_concurrent_rpcs
        self._max_message_size = max_message_size
        self._reflection_enabled = reflection_enabled
        self._health_check_enabled = health_check_enabled

        self._server: aio.Server | None = None
        self._servicers: list[tuple[Any, Callable[[Any, aio.Server], None]]] = []
        self._is_running = False
        self._shutdown_event = asyncio.Event()

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._is_running

    @property
    def address(self) -> str:
        """Get server address."""
        return f"{self._host}:{self._port}"

    def add_servicer(
        self,
        servicer: Any,
        add_func: Callable[[Any, aio.Server], None],
    ) -> None:
        """Register a servicer with the server.

        Args:
            servicer: The servicer instance
            add_func: Function to add servicer to server
        """
        self._servicers.append((servicer, add_func))
        logger.info(
            "grpc_servicer_registered",
            servicer_type=type(servicer).__name__,
        )

    def add_interceptor(self, interceptor: aio.ServerInterceptor) -> None:
        """Add an interceptor to the server.

        Args:
            interceptor: The interceptor to add
        """
        self._interceptors.append(interceptor)
        logger.info(
            "grpc_interceptor_added",
            interceptor_type=type(interceptor).__name__,
        )

    async def start(self) -> None:
        """Start the gRPC server."""
        if self._is_running:
            logger.warning("grpc_server_already_running")
            return

        options = [
            ("grpc.max_send_message_length", self._max_message_size),
            ("grpc.max_receive_message_length", self._max_message_size),
            ("grpc.max_concurrent_streams", self._max_concurrent_rpcs),
            ("grpc.keepalive_time_ms", 7200000),
            ("grpc.keepalive_timeout_ms", 20000),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.http2.max_pings_without_data", 0),
        ]

        self._server = aio.server(
            interceptors=self._interceptors,
            options=options,
            maximum_concurrent_rpcs=self._max_concurrent_rpcs,
        )

        # Register all servicers
        for servicer, add_func in self._servicers:
            add_func(servicer, self._server)

        # Enable reflection if configured
        if self._reflection_enabled:
            await self._enable_reflection()

        # Enable health check if configured
        if self._health_check_enabled:
            await self._enable_health_check()

        # Bind to address
        self._server.add_insecure_port(self.address)

        await self._server.start()
        self._is_running = True
        self._shutdown_event.clear()

        logger.info(
            "grpc_server_started",
            address=self.address,
            reflection_enabled=self._reflection_enabled,
            health_check_enabled=self._health_check_enabled,
            interceptor_count=len(self._interceptors),
            servicer_count=len(self._servicers),
        )

    async def stop(self, grace: float = 5.0) -> None:
        """Gracefully stop the server.

        Args:
            grace: Grace period in seconds for pending RPCs
        """
        if not self._is_running or self._server is None:
            logger.warning("grpc_server_not_running")
            return

        logger.info("grpc_server_stopping", grace_period=grace)

        # Signal shutdown
        self._shutdown_event.set()

        # Stop accepting new RPCs and wait for pending ones
        await self._server.stop(grace)

        self._is_running = False
        self._server = None

        logger.info("grpc_server_stopped")

    async def wait_for_termination(self) -> None:
        """Wait for server termination."""
        if self._server is not None:
            await self._server.wait_for_termination()

    async def _enable_reflection(self) -> None:
        """Enable gRPC reflection service."""
        try:
            from grpc_reflection.v1alpha import reflection

            service_names = [servicer.__class__.__name__ for servicer, _ in self._servicers]
            reflection.enable_server_reflection(service_names, self._server)
            logger.info("grpc_reflection_enabled", services=service_names)
        except ImportError:
            logger.warning("grpc_reflection_not_available")

    async def _enable_health_check(self) -> None:
        """Enable gRPC health check service."""
        try:
            from grpc_health.v1 import health, health_pb2_grpc

            health_servicer = health.HealthServicer()
            health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self._server)
            logger.info("grpc_health_check_enabled")
        except ImportError:
            logger.warning("grpc_health_check_not_available")


async def create_server_from_settings(
    settings: Any,
    interceptors: Sequence[aio.ServerInterceptor] | None = None,
) -> GRPCServer:
    """Create gRPC server from settings.

    Args:
        settings: GRPCServerSettings instance
        interceptors: Optional list of interceptors

    Returns:
        Configured GRPCServer instance
    """
    return GRPCServer(
        host=settings.host,
        port=settings.port,
        interceptors=interceptors,
        max_workers=settings.max_workers,
        max_concurrent_rpcs=settings.max_concurrent_rpcs,
        max_message_size=settings.max_message_size,
        reflection_enabled=settings.reflection_enabled,
        health_check_enabled=settings.health_check_enabled,
    )
