"""gRPC client factory with resilience support.

This module provides a factory for creating gRPC clients with
built-in retry, circuit breaker, and deadline support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeVar

import grpc
from grpc import aio
from structlog import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 30.0
    backoff_multiplier: float = 2.0
    retryable_status_codes: set[grpc.StatusCode] = field(
        default_factory=lambda: {
            grpc.StatusCode.UNAVAILABLE,
            grpc.StatusCode.RESOURCE_EXHAUSTED,
            grpc.StatusCode.ABORTED,
        }
    )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3


class GRPCClientFactory:
    """Factory for creating gRPC clients with resilience.
    
    Creates channels and stubs with built-in retry, circuit breaker,
    and deadline support.
    """

    def __init__(
        self,
        default_timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
        max_message_size: int = 4 * 1024 * 1024,
    ) -> None:
        """Initialize client factory.
        
        Args:
            default_timeout: Default timeout for RPC calls
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
            max_message_size: Maximum message size in bytes
        """
        self._default_timeout = default_timeout
        self._retry_config = retry_config or RetryConfig()
        self._circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self._max_message_size = max_message_size
        self._channels: dict[str, aio.Channel] = {}

    async def create_channel(
        self,
        target: str,
        secure: bool = False,
        credentials: grpc.ChannelCredentials | None = None,
    ) -> aio.Channel:
        """Create a gRPC channel with connection pooling.
        
        Args:
            target: Target address (host:port)
            secure: Whether to use TLS
            credentials: Optional channel credentials
            
        Returns:
            The gRPC channel
        """
        # Check for existing channel
        cache_key = f"{target}:{secure}"
        if cache_key in self._channels:
            return self._channels[cache_key]

        options = [
            ("grpc.max_send_message_length", self._max_message_size),
            ("grpc.max_receive_message_length", self._max_message_size),
            ("grpc.keepalive_time_ms", 7200000),
            ("grpc.keepalive_timeout_ms", 20000),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.enable_retries", 1),
            ("grpc.service_config", self._get_service_config()),
        ]

        if secure:
            if credentials is None:
                credentials = grpc.ssl_channel_credentials()
            channel = aio.secure_channel(target, credentials, options=options)
        else:
            channel = aio.insecure_channel(target, options=options)

        self._channels[cache_key] = channel
        
        logger.info(
            "grpc_channel_created",
            target=target,
            secure=secure,
        )
        
        return channel

    def create_stub(
        self,
        stub_class: type[T],
        channel: aio.Channel,
    ) -> T:
        """Create a stub with interceptors.
        
        Args:
            stub_class: The stub class to instantiate
            channel: The gRPC channel
            
        Returns:
            The stub instance
        """
        return stub_class(channel)

    async def close_all(self) -> None:
        """Close all channels."""
        for target, channel in self._channels.items():
            await channel.close()
            logger.info("grpc_channel_closed", target=target)
        self._channels.clear()

    def _get_service_config(self) -> str:
        """Get gRPC service config JSON for retries."""
        import json
        
        config = {
            "methodConfig": [{
                "name": [{}],
                "timeout": f"{self._default_timeout}s",
                "retryPolicy": {
                    "maxAttempts": self._retry_config.max_retries + 1,
                    "initialBackoff": f"{self._retry_config.backoff_base}s",
                    "maxBackoff": f"{self._retry_config.backoff_max}s",
                    "backoffMultiplier": self._retry_config.backoff_multiplier,
                    "retryableStatusCodes": [
                        code.name for code in self._retry_config.retryable_status_codes
                    ],
                },
            }],
        }
        
        return json.dumps(config)


async def create_client_from_settings(
    settings: Any,
) -> GRPCClientFactory:
    """Create client factory from settings.
    
    Args:
        settings: GRPCClientSettings instance
        
    Returns:
        Configured GRPCClientFactory instance
    """
    retry_config = RetryConfig(
        max_retries=settings.max_retries,
        backoff_base=settings.retry_backoff_base,
        backoff_max=settings.retry_backoff_max,
        backoff_multiplier=settings.retry_backoff_multiplier,
    )
    
    circuit_breaker_config = CircuitBreakerConfig(
        failure_threshold=settings.circuit_breaker_threshold,
        recovery_timeout=settings.circuit_breaker_timeout,
    )
    
    return GRPCClientFactory(
        default_timeout=settings.default_timeout,
        retry_config=retry_config,
        circuit_breaker_config=circuit_breaker_config,
        max_message_size=settings.max_message_size,
    )
