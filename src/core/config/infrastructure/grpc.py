"""gRPC configuration settings.

This module provides configuration classes for gRPC server and client settings,
following the existing Pydantic Settings pattern used in the project.

**Feature: core-config-restructuring-2025**
"""

from pydantic import BaseModel, Field


class GRPCServerSettings(BaseModel):
    """gRPC server configuration.

    Note:
        Default host '0.0.0.0' binds to all interfaces. In production,
        consider using '127.0.0.1' for localhost-only or a specific IP.
    """

    enabled: bool = Field(default=False, description="Enable gRPC server")
    host: str = Field(
        default="0.0.0.0",
        description="gRPC server host (use 127.0.0.1 for localhost-only)",
    )
    port: int = Field(default=50051, ge=1, le=65535, description="gRPC server port")
    max_workers: int = Field(default=10, ge=1, le=100, description="Maximum worker threads")
    max_concurrent_rpcs: int = Field(default=100, ge=1, le=10000, description="Maximum concurrent RPCs")
    reflection_enabled: bool = Field(default=True, description="Enable gRPC reflection for debugging")
    health_check_enabled: bool = Field(default=True, description="Enable gRPC health check service")
    max_message_size: int = Field(default=4 * 1024 * 1024, ge=1024, description="Maximum message size in bytes (4MB)")
    keepalive_time_ms: int = Field(default=7200000, ge=0, description="Keepalive time in milliseconds")
    keepalive_timeout_ms: int = Field(default=20000, ge=0, description="Keepalive timeout in milliseconds")


class GRPCClientSettings(BaseModel):
    """gRPC client configuration."""

    default_timeout: float = Field(default=30.0, description="Default timeout for RPC calls in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_backoff_base: float = Field(default=1.0, description="Base delay for exponential backoff in seconds")
    retry_backoff_max: float = Field(default=30.0, description="Maximum delay for exponential backoff in seconds")
    retry_backoff_multiplier: float = Field(default=2.0, description="Multiplier for exponential backoff")
    circuit_breaker_threshold: int = Field(
        default=5, ge=1, le=100, description="Failure threshold to open circuit breaker"
    )
    circuit_breaker_timeout: float = Field(
        default=30.0, description="Time in seconds before circuit breaker half-opens"
    )
    max_message_size: int = Field(default=4 * 1024 * 1024, description="Maximum message size in bytes (4MB)")
    enable_retry: bool = Field(default=True, description="Enable automatic retries")
    enable_circuit_breaker: bool = Field(default=True, description="Enable circuit breaker pattern")


class GRPCSettings(BaseModel):
    """Combined gRPC settings."""

    server: GRPCServerSettings = Field(default_factory=GRPCServerSettings)
    client: GRPCClientSettings = Field(default_factory=GRPCClientSettings)
