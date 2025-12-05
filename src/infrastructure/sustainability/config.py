"""
Configuration module for sustainability services.

Provides settings for carbon intensity, electricity pricing,
and external API configurations.
"""

from decimal import Decimal

from pydantic import Field
from pydantic_settings import BaseSettings


class SustainabilitySettings(BaseSettings):
    """Settings for sustainability module."""

    # Electricity pricing
    electricity_price_per_kwh: Decimal = Field(
        default=Decimal("0.12"),
        description="Default electricity price per kWh in USD",
    )
    currency: str = Field(default="USD", description="Currency for cost calculations")

    # Carbon intensity defaults
    default_carbon_intensity_gco2_per_kwh: Decimal = Field(
        default=Decimal("400"),
        description="Default carbon intensity when regional data unavailable",
    )
    default_region: str = Field(
        default="global",
        description="Default region identifier",
    )

    # External API configuration
    carbon_intensity_api_url: str = Field(
        default="https://api.electricitymap.org/v3",
        description="Carbon intensity API base URL",
    )
    carbon_intensity_api_key: str | None = Field(
        default=None,
        description="API key for carbon intensity service",
    )
    carbon_intensity_timeout_seconds: int = Field(
        default=10,
        description="Timeout for carbon intensity API calls",
    )

    # Prometheus configuration
    prometheus_url: str = Field(
        default="http://prometheus:9090",
        description="Prometheus server URL",
    )
    prometheus_timeout_seconds: int = Field(
        default=30,
        description="Timeout for Prometheus queries",
    )

    # Circuit breaker configuration
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        description="Number of failures before circuit opens",
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60,
        description="Seconds before attempting recovery",
    )

    # Kepler metrics configuration
    kepler_namespace: str = Field(
        default="kepler-system",
        description="Namespace where Kepler is deployed",
    )
    kepler_metrics_port: int = Field(
        default=9102,
        description="Port for Kepler metrics endpoint",
    )

    model_config = {"env_prefix": "SUSTAINABILITY_"}


def get_sustainability_settings() -> SustainabilitySettings:
    """Get sustainability settings instance."""
    return SustainabilitySettings()
