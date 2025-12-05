"""Base servicer class with DI integration.

This module provides a base class for gRPC servicers that integrates
with the dependency injection container and application layer.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, TypeVar

from grpc import aio
from structlog import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

logger = get_logger(__name__)

T = TypeVar("T")


class BaseServicer(ABC):
    """Base class for gRPC servicers with DI support.
    
    This class provides common functionality for all gRPC servicers
    including dependency injection, error handling, and logging.
    """

    def __init__(self, container: Any | None = None) -> None:
        """Initialize base servicer.
        
        Args:
            container: Optional DI container instance
        """
        self._container = container
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

    async def handle_unary(
        self,
        request: Any,
        context: aio.ServicerContext,
        handler: Callable[..., Any],
    ) -> Any:
        """Handle unary RPC with error handling.
        
        Args:
            request: The request message
            context: The servicer context
            handler: The handler function
            
        Returns:
            The response message
        """
        method = context.invocation_metadata()
        self._logger.info(
            "grpc_unary_request",
            method=str(method),
            request_type=type(request).__name__,
        )
        
        try:
            result = await handler(request, context)
            self._logger.info(
                "grpc_unary_response",
                response_type=type(result).__name__,
            )
            return result
        except Exception as exc:
            self._logger.error(
                "grpc_unary_error",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

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
        self._logger.info(
            "grpc_server_stream_start",
            request_type=type(request).__name__,
        )
        
        message_count = 0
        try:
            async for message in handler(request, context):
                message_count += 1
                yield message
                
            self._logger.info(
                "grpc_server_stream_complete",
                message_count=message_count,
            )
        except Exception as exc:
            self._logger.error(
                "grpc_server_stream_error",
                error=str(exc),
                message_count=message_count,
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
        self._logger.info("grpc_client_stream_start")
        
        messages: list[Any] = []
        try:
            async for message in request_iterator:
                messages.append(message)
                
            self._logger.info(
                "grpc_client_stream_received",
                message_count=len(messages),
            )
            
            result = await handler(messages, context)
            return result
        except Exception as exc:
            self._logger.error(
                "grpc_client_stream_error",
                error=str(exc),
                message_count=len(messages),
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
        self._logger.info("grpc_bidi_stream_start")
        
        sent_count = 0
        try:
            async for message in handler(request_iterator, context):
                sent_count += 1
                yield message
                
            self._logger.info(
                "grpc_bidi_stream_complete",
                sent_count=sent_count,
            )
        except Exception as exc:
            self._logger.error(
                "grpc_bidi_stream_error",
                error=str(exc),
                sent_count=sent_count,
            )
            raise
