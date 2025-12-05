"""OpenTelemetry tracing interceptor for gRPC.

This module provides an interceptor that creates OpenTelemetry
spans for gRPC requests and propagates trace context.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from grpc import StatusCode, aio
from structlog import get_logger

logger = get_logger(__name__)

# Trace context headers
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"


class TracingInterceptor(aio.ServerInterceptor):
    """OpenTelemetry tracing interceptor.
    
    Creates spans for gRPC calls and propagates trace context.
    """

    def __init__(
        self,
        service_name: str = "grpc-service",
        tracer: Any | None = None,
    ) -> None:
        """Initialize tracing interceptor.
        
        Args:
            service_name: Name of the service for spans
            tracer: Optional OpenTelemetry tracer instance
        """
        self._service_name = service_name
        self._tracer = tracer or self._get_default_tracer()

    def _get_default_tracer(self) -> Any:
        """Get default OpenTelemetry tracer."""
        try:
            from opentelemetry import trace
            return trace.get_tracer(self._service_name)
        except ImportError:
            logger.warning("opentelemetry not installed, tracing disabled")
            return None

    async def intercept_service(
        self,
        continuation: Callable[..., Any],
        handler_call_details: aio.HandlerCallDetails,
    ) -> aio.RpcMethodHandler:
        """Intercept and trace gRPC requests.
        
        Args:
            continuation: The next handler in chain
            handler_call_details: Details about the RPC call
            
        Returns:
            The RPC method handler
        """
        if self._tracer is None:
            return await continuation(handler_call_details)

        method = handler_call_details.method
        metadata = dict(handler_call_details.invocation_metadata or [])
        
        # Extract trace context from metadata
        context = self._extract_context(metadata)
        
        # Create span
        try:
            from opentelemetry import trace
            from opentelemetry.trace import SpanKind
            
            with self._tracer.start_as_current_span(
                name=method,
                kind=SpanKind.SERVER,
                context=context,
            ) as span:
                span.set_attribute("rpc.system", "grpc")
                span.set_attribute("rpc.service", self._service_name)
                span.set_attribute("rpc.method", method)
                
                try:
                    handler = await continuation(handler_call_details)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return handler
                except Exception as exc:
                    span.set_status(
                        trace.Status(trace.StatusCode.ERROR, str(exc))
                    )
                    span.record_exception(exc)
                    raise
        except ImportError:
            return await continuation(handler_call_details)

    def _extract_context(self, metadata: dict[str, str]) -> Any:
        """Extract trace context from metadata.
        
        Args:
            metadata: The gRPC metadata
            
        Returns:
            OpenTelemetry context or None
        """
        try:
            from opentelemetry.propagate import extract
            
            # Convert metadata to carrier format
            carrier = {
                TRACEPARENT_HEADER: metadata.get(TRACEPARENT_HEADER, ""),
                TRACESTATE_HEADER: metadata.get(TRACESTATE_HEADER, ""),
            }
            
            return extract(carrier)
        except ImportError:
            return None


def inject_trace_context(metadata: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Inject trace context into metadata for outgoing calls.
    
    Args:
        metadata: The gRPC metadata list
        
    Returns:
        Metadata with trace context injected
    """
    try:
        from opentelemetry.propagate import inject
        
        carrier: dict[str, str] = {}
        inject(carrier)
        
        result = list(metadata)
        for key, value in carrier.items():
            result.append((key, value))
        
        return result
    except ImportError:
        return metadata


def get_current_trace_id() -> str | None:
    """Get current trace ID if available.
    
    Returns:
        The current trace ID or None
    """
    try:
        from opentelemetry import trace
        
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().trace_id, "032x")
        return None
    except ImportError:
        return None
