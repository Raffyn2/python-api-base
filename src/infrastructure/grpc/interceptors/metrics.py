"""Prometheus metrics interceptor for gRPC.

This module provides an interceptor that records gRPC metrics
for Prometheus monitoring.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from grpc import aio
from structlog import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

logger = get_logger(__name__)


class MetricsInterceptor(aio.ServerInterceptor):
    """Prometheus metrics interceptor.

    Records request count, latency, and status for gRPC calls.
    """

    def __init__(
        self,
        namespace: str = "grpc",
        subsystem: str = "server",
    ) -> None:
        """Initialize metrics interceptor.

        Args:
            namespace: Prometheus metric namespace
            subsystem: Prometheus metric subsystem
        """
        self._namespace = namespace
        self._subsystem = subsystem
        self._metrics = self._create_metrics()

    def _create_metrics(self) -> dict[str, Any]:
        """Create Prometheus metrics."""
        try:
            from prometheus_client import Counter, Histogram

            return {
                "requests_total": Counter(
                    f"{self._namespace}_{self._subsystem}_requests_total",
                    "Total number of gRPC requests",
                    ["method", "status"],
                ),
                "request_duration_seconds": Histogram(
                    f"{self._namespace}_{self._subsystem}_request_duration_seconds",
                    "gRPC request duration in seconds",
                    ["method"],
                    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
                ),
                "requests_in_progress": None,  # Gauge for in-progress requests
            }
        except ImportError:
            logger.warning("prometheus_client not installed, metrics disabled")
            return {}

    async def intercept_service(
        self,
        continuation: Callable[..., Any],
        handler_call_details: aio.HandlerCallDetails,
    ) -> aio.RpcMethodHandler:
        """Intercept and record metrics for gRPC requests.

        Args:
            continuation: The next handler in chain
            handler_call_details: Details about the RPC call

        Returns:
            The RPC method handler
        """
        if not self._metrics:
            return await continuation(handler_call_details)

        method = handler_call_details.method
        start_time = time.perf_counter()
        status = "OK"

        try:
            handler = await continuation(handler_call_details)
            return self._wrap_handler(handler, method, start_time)
        except Exception as exc:
            status = self._get_status_from_exception(exc)
            self._record_metrics(method, status, start_time)
            raise

    def _wrap_handler(
        self,
        handler: aio.RpcMethodHandler,
        method: str,
        start_time: float,
    ) -> aio.RpcMethodHandler:
        """Wrap handler to record metrics on completion."""
        if handler is None:
            return handler

        original_unary_unary = handler.unary_unary

        async def metered_unary_unary(
            request: Any,
            context: aio.ServicerContext,
        ) -> Any:
            try:
                result = await original_unary_unary(request, context)
                self._record_metrics(method, "OK", start_time)
                return result
            except Exception as exc:
                status = self._get_status_from_exception(exc)
                self._record_metrics(method, status, start_time)
                raise

        return aio.RpcMethodHandler(
            request_streaming=handler.request_streaming,
            response_streaming=handler.response_streaming,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
            unary_unary=metered_unary_unary if original_unary_unary else None,
            unary_stream=handler.unary_stream,
            stream_unary=handler.stream_unary,
            stream_stream=handler.stream_stream,
        )

    def _record_metrics(
        self,
        method: str,
        status: str,
        start_time: float,
    ) -> None:
        """Record metrics for a completed request."""
        duration = time.perf_counter() - start_time

        if self._metrics.get("requests_total"):
            self._metrics["requests_total"].labels(
                method=method,
                status=status,
            ).inc()

        if self._metrics.get("request_duration_seconds"):
            self._metrics["request_duration_seconds"].labels(
                method=method,
            ).observe(duration)

    def _get_status_from_exception(self, exc: Exception) -> str:
        """Get status string from exception."""
        if hasattr(exc, "code") and callable(exc.code):
            return exc.code().name
        return "UNKNOWN"
