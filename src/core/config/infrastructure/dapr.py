"""Dapr configuration settings.

This module provides configuration for Dapr sidecar integration.

**Feature: core-config-restructuring-2025**
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DaprSettings(BaseSettings):
    """Dapr configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="DAPR_",
        env_file=".env",
        extra="ignore",
    )

    enabled: bool = Field(
        default=True,
        description="Enable Dapr integration",
    )
    http_endpoint: str = Field(
        default="http://localhost:3500",
        description="Dapr HTTP endpoint",
    )
    grpc_endpoint: str = Field(
        default="localhost:50001",
        description="Dapr gRPC endpoint",
    )
    api_token: str | None = Field(
        default=None,
        description="Dapr API token for authentication",
    )
    app_id: str = Field(
        default="python-api",
        description="Application ID for Dapr",
    )
    app_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Application port for Dapr callbacks",
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Default timeout for Dapr operations (1-3600 seconds)",
    )
    state_store_name: str = Field(
        default="statestore",
        description="Default state store component name",
    )
    pubsub_name: str = Field(
        default="pubsub",
        description="Default pub/sub component name",
    )
    secret_store_name: str = Field(
        default="secretstore",
        description="Default secret store component name",
    )
    health_check_enabled: bool = Field(
        default=True,
        description="Enable Dapr health checks",
    )
    wait_for_sidecar: bool = Field(
        default=True,
        description="Wait for sidecar on startup",
    )
    sidecar_wait_timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Timeout for waiting for sidecar (1-300 seconds)",
    )
    tracing_enabled: bool = Field(
        default=True,
        description="Enable distributed tracing",
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )


@lru_cache
def get_dapr_settings() -> DaprSettings:
    """Get cached Dapr settings.

    Returns:
        DaprSettings: Dapr configuration instance.
    """
    return DaprSettings()
