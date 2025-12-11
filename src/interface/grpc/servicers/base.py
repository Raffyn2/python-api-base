"""Base servicer class with DI integration.

This module provides a base class for gRPC servicers that integrates
with the dependency injection container, CQRS buses, and observability.

**Feature: interface-modules-workflow-analysis**
"""

from __future__ import annotations

import time
from abc import ABC
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import uuid4

from grpc import StatusCode
from structlog import get_logger

from interface.errors.exceptions import (
    NotFoundError,
    ValidationError,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from grpc import aio

    from application.common.cqrs import CommandBus, QueryBus

logger = get_logger(__name__)

T = TypeVar("T")

# Constants
_CORRELATION_ID_HEADER = "x-correlation-id"
_ERR_INTERNAL = "Internal server error"
_ERR_NOT_FOUND = "Resource not found"
_ERR_VALIDATION = "Validation failed"
_ERR_FORBIDDEN = "Access denied"
_ERR_UNAUTHENTICATED = "Authentication required"

# Error type to gRPC status mapping
_ERROR_STATUS_MAP: dict[type[Exception], StatusCode] = {
    NotFoundError: StatusCode.NOT_FOUND,
    ValidationError: StatusCode.INVALID_ARGUMENT,
}


class BaseServicer(ABC):
    """Base class for gRPC servicers with DI support.

    Provides common functionality for all gRPC servicers:
    - Dependency injection integration
    - CQRS bus access (QueryBus, CommandBus)
    - Structured logging with correlation IDs
    - Error sanitization for clients

    **Feature: interface-modules-workflow-analysis**
    """

    def __init__(
        self,
        container: Any | None = None,
        query_bus: QueryBus | None = None,
        command_bus: CommandBus | None = None,
    ) -> None:
        """Initialize base servicer.

        Args:
            container: Optional DI container instance
            query_bus: Optional QueryBus for CQRS queries
            command_bus: Optional CommandBus for CQRS commands
        """
        self._container = container
        self._query_bus = query_bus
        self._command_bus = command_bus
        self._logger = get_logger(self.__class__.__name__)

    def get_use_case(self, use_case_type: type[T]) -> T:
        """Get a use case from the DI container.

        Args:
            use_case_type: The type of use case to resolve

        Returns:
            The resolved use case instance

        Raises:
            RuntimeError: If container is not configured
        """
        if self._container is None:
            raise RuntimeError("DI container not configured")
        return self._container.resolve(use_case_type)

    def get_service(self, service_type: type[T]) -> T:
        """Get a service from the DI container.

        Args:
            service_type: The type of service to resolve

        Returns:
            The resolved service instance

        Raises:
            RuntimeError: If container is not configured
        """
        if self._container is None:
            raise RuntimeError("DI container not configured")
        return self._container.resolve(service_type)

    @property
    def query_bus(self) -> QueryBus:
        """Get QueryBus for CQRS queries.

        Raises:
            RuntimeError: If QueryBus not configured
        """
        if self._query_bus is None:
            raise RuntimeError("QueryBus not configured")
        return self._query_bus

    @property
    def command_bus(self) -> CommandBus:
        """Get CommandBus for CQRS commands.

        Raises:
            RuntimeError: If CommandBus not configured
        """
        if self._command_bus is None:
            raise RuntimeError("CommandBus not configured")
        return self._command_bus

    def _get_correlation_id(self, context: aio.ServicerContext) -> str:
        """Extract or generate correlation ID from context.

        Args:
            context: The servicer context

        Returns:
            Correlation ID string
        """
        metadata = dict(context.invocation_metadata() or [])
        return metadata.get(_CORRELATION_ID_HEADER, str(uuid4()))

    def _sanitize_error(self, error: Exception) -> str:
        """Sanitize error message for client response.

        Uses type checking first, then falls back to name matching.

        Args:
            error: The exception to sanitize

        Returns:
            Safe error message for client
        """
        # Check known types first
        if isinstance(error, NotFoundError):
            return _ERR_NOT_FOUND
        if isinstance(error, ValidationError):
            return _ERR_VALIDATION

        # Fallback to name matching for external exceptions
        error_type = type(error).__name__
        if "NotFound" in error_type:
            return _ERR_NOT_FOUND
        if "Validation" in error_type or "Invalid" in error_type:
            return _ERR_VALIDATION
        if "Permission" in error_type or "Forbidden" in error_type:
            return _ERR_FORBIDDEN
        if "Unauthorized" in error_type or "Auth" in error_type:
            return _ERR_UNAUTHENTICATED
        return _ERR_INTERNAL

    def _get_grpc_status(self, error: Exception) -> StatusCode:
        """Map exception to gRPC status code.

        Uses type checking first, then falls back to name matching.

        Args:
            error: The exception to map

        Returns:
            Appropriate gRPC StatusCode
        """
        # Check registered types first
        for error_type, status in _ERROR_STATUS_MAP.items():
            if isinstance(error, error_type):
                return status

        # Fallback to name matching for external exceptions
        error_name = type(error).__name__
        if "NotFound" in error_name:
            return StatusCode.NOT_FOUND
        if "Validation" in error_name or "Invalid" in error_name:
            return StatusCode.INVALID_ARGUMENT
        if "Permission" in error_name or "Forbidden" in error_name:
            return StatusCode.PERMISSION_DENIED
        if "Unauthorized" in error_name or "Auth" in error_name:
            return StatusCode.UNAUTHENTICATED
        return StatusCode.INTERNAL

    def _log_request(
        self,
        event: str,
        correlation_id: str,
        **kwargs: Any,
    ) -> None:
        """Log request event with correlation ID.

        Args:
            event: Event name
            correlation_id: Correlation ID
            **kwargs: Additional log fields
        """
        self._logger.info(event, correlation_id=correlation_id, **kwargs)

    def _log_error(
        self,
        event: str,
        error: Exception,
        correlation_id: str,
        **kwargs: Any,
    ) -> None:
        """Log error event with correlation ID.

        Args:
            event: Event name
            error: The exception
            correlation_id: Correlation ID
            **kwargs: Additional log fields
        """
        self._logger.error(
            event,
            error_type=type(error).__name__,
            correlation_id=correlation_id,
            **kwargs,
        )

    async def handle_unary(
        self,
        request: Any,
        context: aio.ServicerContext,
        handler: Callable[..., Any],
    ) -> Any:
        """Handle unary RPC with error handling and logging.

        Args:
            request: The request message
            context: The servicer context
            handler: The handler function

        Returns:
            The response message
        """
        correlation_id = self._get_correlation_id(context)
        start_time = time.perf_counter()

        self._log_request(
            "grpc_unary_request",
            correlation_id,
            request_type=type(request).__name__,
        )

        try:
            result = await handler(request, context)
            duration_ms = (time.perf_counter() - start_time) * 1000

            self._log_request(
                "grpc_unary_response",
                correlation_id,
                response_type=type(result).__name__,
                duration_ms=round(duration_ms, 2),
            )
            return result
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000

            self._log_error(
                "grpc_unary_error",
                exc,
                correlation_id,
                duration_ms=round(duration_ms, 2),
            )
            await context.abort(
                self._get_grpc_status(exc),
                self._sanitize_error(exc),
            )

    async def handle_server_stream(
        self,
        request: Any,
        context: aio.ServicerContext,
        handler: Callable[..., AsyncIterator[Any]],
    ) -> AsyncIterator[Any]:
        """Handle server streaming RPC.

        Args:
            request: The request message
            context: The servicer context
            handler: The async generator handler

        Yields:
            Response messages
        """
        correlation_id = self._get_correlation_id(context)
        start_time = time.perf_counter()

        self._log_request(
            "grpc_server_stream_start",
            correlation_id,
            request_type=type(request).__name__,
        )

        message_count = 0
        try:
            async for message in handler(request, context):
                message_count += 1
                yield message

            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_request(
                "grpc_server_stream_complete",
                correlation_id,
                message_count=message_count,
                duration_ms=round(duration_ms, 2),
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_error(
                "grpc_server_stream_error",
                exc,
                correlation_id,
                message_count=message_count,
                duration_ms=round(duration_ms, 2),
            )
            raise

    async def handle_client_stream(
        self,
        request_iterator: AsyncIterator[Any],
        context: aio.ServicerContext,
        handler: Callable[..., Any],
    ) -> Any:
        """Handle client streaming RPC.

        Args:
            request_iterator: Iterator of request messages
            context: The servicer context
            handler: The handler function

        Returns:
            The response message
        """
        correlation_id = self._get_correlation_id(context)
        start_time = time.perf_counter()

        self._log_request("grpc_client_stream_start", correlation_id)

        messages: list[Any] = []
        try:
            messages = [message async for message in request_iterator]

            self._log_request(
                "grpc_client_stream_received",
                correlation_id,
                message_count=len(messages),
            )

            result = await handler(messages, context)
            duration_ms = (time.perf_counter() - start_time) * 1000

            self._log_request(
                "grpc_client_stream_complete",
                correlation_id,
                message_count=len(messages),
                duration_ms=round(duration_ms, 2),
            )
            return result
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_error(
                "grpc_client_stream_error",
                exc,
                correlation_id,
                message_count=len(messages),
                duration_ms=round(duration_ms, 2),
            )
            raise

    async def handle_bidi_stream(
        self,
        request_iterator: AsyncIterator[Any],
        context: aio.ServicerContext,
        handler: Callable[..., AsyncIterator[Any]],
    ) -> AsyncIterator[Any]:
        """Handle bidirectional streaming RPC.

        Args:
            request_iterator: Iterator of request messages
            context: The servicer context
            handler: The async generator handler

        Yields:
            Response messages
        """
        correlation_id = self._get_correlation_id(context)
        start_time = time.perf_counter()

        self._log_request("grpc_bidi_stream_start", correlation_id)

        sent_count = 0
        try:
            async for message in handler(request_iterator, context):
                sent_count += 1
                yield message

            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_request(
                "grpc_bidi_stream_complete",
                correlation_id,
                sent_count=sent_count,
                duration_ms=round(duration_ms, 2),
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._log_error(
                "grpc_bidi_stream_error",
                exc,
                correlation_id,
                sent_count=sent_count,
                duration_ms=round(duration_ms, 2),
            )
            raise
