"""Error handling interceptor for gRPC.

This module provides an interceptor that catches exceptions
and converts them to appropriate gRPC status codes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from grpc import aio
from structlog import get_logger

from infrastructure.grpc.utils.status import exception_to_status

if TYPE_CHECKING:
    from collections.abc import Callable

logger = get_logger(__name__)


class ErrorInterceptor(aio.ServerInterceptor):
    """Error handling interceptor.

    Catches exceptions and converts them to gRPC status codes
    with proper error details.
    """

    def __init__(
        self,
        include_stack_trace: bool = False,
        log_errors: bool = True,
    ) -> None:
        """Initialize error interceptor.

        Args:
            include_stack_trace: Include stack trace in error details
            log_errors: Log errors when they occur
        """
        self._include_stack_trace = include_stack_trace
        self._log_errors = log_errors

    async def intercept_service(
        self,
        continuation: Callable[..., Any],
        handler_call_details: aio.HandlerCallDetails,
    ) -> aio.RpcMethodHandler:
        """Intercept and handle errors in gRPC requests.

        Args:
            continuation: The next handler in chain
            handler_call_details: Details about the RPC call

        Returns:
            The RPC method handler
        """
        method = handler_call_details.method

        try:
            handler = await continuation(handler_call_details)
            return self._wrap_handler(handler, method)
        except Exception as exc:
            return self._create_error_handler(exc, method)

    def _wrap_handler(
        self,
        handler: aio.RpcMethodHandler,
        method: str,
    ) -> aio.RpcMethodHandler:
        """Wrap handler to catch and convert errors."""
        if handler is None:
            return handler

        original_unary_unary = handler.unary_unary

        async def error_handled_unary_unary(
            request: Any,
            context: aio.ServicerContext,
        ) -> Any:
            try:
                return await original_unary_unary(request, context)
            except Exception as exc:
                await self._handle_error(exc, context, method)
                raise

        return aio.RpcMethodHandler(
            request_streaming=handler.request_streaming,
            response_streaming=handler.response_streaming,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
            unary_unary=error_handled_unary_unary if original_unary_unary else None,
            unary_stream=handler.unary_stream,
            stream_unary=handler.stream_unary,
            stream_stream=handler.stream_stream,
        )

    def _create_error_handler(
        self,
        exc: Exception,
        method: str,
    ) -> aio.RpcMethodHandler:
        """Create a handler that returns the error."""

        async def error_handler(
            request: Any,
            context: aio.ServicerContext,
        ) -> None:
            await self._handle_error(exc, context, method)

        return aio.unary_unary_rpc_method_handler(error_handler)

    async def _handle_error(
        self,
        exc: Exception,
        context: aio.ServicerContext,
        method: str,
    ) -> None:
        """Handle an exception by setting gRPC status.

        Args:
            exc: The exception that occurred
            context: The servicer context
            method: The RPC method name
        """
        status_code, message = exception_to_status(exc)

        if self._log_errors:
            logger.error(
                "grpc_error",
                method=method,
                error_type=type(exc).__name__,
                status_code=status_code.name,
                exc_info=exc,
            )

        # Build error details
        details = message
        if self._include_stack_trace:
            import traceback

            details = f"{message}\n{traceback.format_exc()}"

        await context.abort(status_code, details)
