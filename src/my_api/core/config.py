"""Configuration management with Pydantic Settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE__")

    url: str = Field(
        default="postgresql+asyncpg://localhost/mydb",
        description="Database connection URL",
    )
    pool_size: int = Field(default=5, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(
        default=10, ge=0, le=100, description="Max overflow connections"
    )
    echo: bool = Field(default=False, description="Echo SQL statements")


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    model_config = SettingsConfigDict(env_prefix="SECURITY__")

    secret_key: SecretStr = Field(
        ...,
        description="Secret key for signing tokens",
        min_length=32,
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    rate_limit: str = Field(
        default="100/minute",
        description="Rate limit configuration",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Access token expiration in minutes"
    )


class ObservabilitySettings(BaseSettings):
    """Observability configuration settings."""

    model_config = SettingsConfigDict(env_prefix="OBSERVABILITY__")

    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )
    log_format: str = Field(
        default="json",
        description="Log output format (json or console)",
        pattern="^(json|console)$",
    )
    otlp_endpoint: str | None = Field(
        default=None,
        description="OpenTelemetry collector endpoint",
    )
    service_name: str = Field(
        default="my-api",
        description="Service name for tracing",
    )
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")


class Settings(BaseSettings):
    """Application settings with nested configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = Field(default="My API", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    version: str = Field(default="0.1.0", description="API version")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    # Nested settings
    database: Annotated[DatabaseSettings, Field(default_factory=DatabaseSettings)]
    security: Annotated[SecuritySettings, Field(default_factory=SecuritySettings)]
    observability: Annotated[
        ObservabilitySettings, Field(default_factory=ObservabilitySettings)
    ]


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
