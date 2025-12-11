"""Logging interceptor for gRPC.

This module provides an interceptor that logs gRPC requests
and responses with correlation IDs.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any

from grpc import aio
from structlog import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

logger = get_logger(__name__)

CORRELATION_ID_HEADER = "x-correlation-id"


class LoggingInterceptor(aio.ServerInterceptor):
    """Request/response logging interceptor.

    Logs all gRPC requests with timing and correlation IDs.
    """

    def __init__(
        self,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ) -> None:
        """Initialize logging interceptor.

        Args:
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
        """
        self._log_request_body = log_request_body
        self._log_response_body = log_response_body

    async def intercept_service(
        self,
        continuation: Callable[..., Any],
        handler_call_details: aio.HandlerCallDetails,
    ) -> aio.RpcMethodHandler:
        """Intercept and log gRPC requests.

        Args:
            continuation: The next handler in chain
            handler_call_details: Details about the RPC call

        Returns:
            The RPC method handler
        """
        method = handler_call_details.method
        metadata = dict(handler_call_details.invocation_metadata or [])

        # Get or generate correlation ID
        correlation_id = metadata.get(CORRELATION_ID_HEADER, str(uuid.uuid4()))

        start_time = time.perf_counter()

        logger.info(
            "grpc_request_started",
            method=method,
            correlation_id=correlation_id,
        )

        try:
            handler = await continuation(handler_call_details)

            # Wrap the handler to log completion
            return self._wrap_handler(
                handler,
                method,
                correlation_id,
                start_time,
            )
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "grpc_request_failed",
                method=method,
                correlation_id=correlation_id,
                duration_ms=duration_ms,
            )
            raise

    def _wrap_handler(
        self,
        handler: aio.RpcMethodHandler,
        method: str,
        correlation_id: str,
        start_time: float,
    ) -> aio.RpcMethodHandler:
        """Wrap handler to log completion.

        Args:
            handler: The original handler
            method: The RPC method name
            correlation_id: The correlation ID
            start_time: Request start time

        Returns:
            Wrapped handler
        """
        if handler is None:
            return handler

        ctx = _LogContext(self, method, correlation_id, start_time)
        return aio.RpcMethodHandler(
            request_streaming=handler.request_streaming,
            response_streaming=handler.response_streaming,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
            unary_unary=ctx.wrap_unary_unary(handler.unary_unary),
            unary_stream=ctx.wrap_unary_stream(handler.unary_stream),
            stream_unary=ctx.wrap_stream_unary(handler.stream_unary),
            stream_stream=ctx.wrap_stream_stream(handler.stream_stream),
        )

    def _log_success(
        self,
        method: str,
        correlation_id: str,
        start_time: float,
    ) -> None:
        """Log successful request completion."""
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "grpc_request_completed",
            method=method,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            status="OK",
        )

    def _log_error(
        self,
        method: str,
        correlation_id: str,
        start_time: float,
        exc: Exception,
    ) -> None:
        """Log failed request."""
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "grpc_request_failed",
            method=method,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
            exc_info=exc,
        )


class _LogContext:
    """Helper class to wrap gRPC handlers with logging."""

    def __init__(
        self,
        interceptor: LoggingInterceptor,
        method: str,
        correlation_id: str,
        start_time: float,
    ) -> None:
        self._interceptor = interceptor
        self._method = method
        self._correlation_id = correlation_id
        self._start_time = start_time

    def wrap_unary_unary(self, handler: Any) -> Any:
        """Wrap unary-unary handler."""
        if handler is None:
            return None

        async def wrapped(request: Any, context: aio.ServicerContext) -> Any:
            try:
                result = await handler(request, context)
                self._interceptor._log_success(self._method, self._correlation_id, self._start_time)
                return result
            except Exception as exc:
                self._interceptor._log_error(self._method, self._correlation_id, self._start_time, exc)
                raise

        return wrapped

    def wrap_unary_stream(self, handler: Any) -> Any:
        """Wrap unary-stream handler."""
        if handler is None:
            return None

        async def wrapped(request: Any, context: aio.ServicerContext) -> Any:
            try:
                async for item in handler(request, context):
                    yield item
                self._interceptor._log_success(self._method, self._correlation_id, self._start_time)
            except Exception as exc:
                self._interceptor._log_error(self._method, self._correlation_id, self._start_time, exc)
                raise

        return wrapped

    def wrap_stream_unary(self, handler: Any) -> Any:
        """Wrap stream-unary handler."""
        if handler is None:
            return None

        async def wrapped(request_iterator: Any, context: aio.ServicerContext) -> Any:
            try:
                result = await handler(request_iterator, context)
                self._interceptor._log_success(self._method, self._correlation_id, self._start_time)
                return result
            except Exception as exc:
                self._interceptor._log_error(self._method, self._correlation_id, self._start_time, exc)
                raise

        return wrapped

    def wrap_stream_stream(self, handler: Any) -> Any:
        """Wrap stream-stream handler."""
        if handler is None:
            return None

        async def wrapped(request_iterator: Any, context: aio.ServicerContext) -> Any:
            try:
                async for item in handler(request_iterator, context):
                    yield item
                self._interceptor._log_success(self._method, self._correlation_id, self._start_time)
            except Exception as exc:
                self._interceptor._log_error(self._method, self._correlation_id, self._start_time, exc)
                raise

        return wrapped
