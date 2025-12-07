"""Tests for sustainability configuration.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from decimal import Decimal

import pytest

from infrastructure.sustainability.config import (
    SustainabilitySettings,
    get_sustainability_settings,
)


class TestSustainabilitySettings:
    """Tests for SustainabilitySettings."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = SustainabilitySettings()
        assert settings.electricity_price_per_kwh == Decimal("0.12")
        assert settings.currency == "USD"
        assert settings.default_carbon_intensity_gco2_per_kwh == Decimal("400")
        assert settings.default_region == "global"
        assert settings.carbon_intensity_api_url == "https://api.electricitymap.org/v3"
        assert settings.carbon_intensity_api_key is None
        assert settings.carbon_intensity_timeout_seconds == 10
        assert settings.prometheus_url == "http://prometheus:9090"
        assert settings.prometheus_timeout_seconds == 30
        assert settings.circuit_breaker_failure_threshold == 5
        assert settings.circuit_breaker_recovery_timeout == 60
        assert settings.kepler_namespace == "kepler-system"
        assert settings.kepler_metrics_port == 9102

    def test_custom_electricity_pricing(self) -> None:
        """Test custom electricity pricing configuration."""
        settings = SustainabilitySettings(
            electricity_price_per_kwh=Decimal("0.25"),
            currency="EUR",
        )
        assert settings.electricity_price_per_kwh == Decimal("0.25")
        assert settings.currency == "EUR"

    def test_custom_carbon_intensity(self) -> None:
        """Test custom carbon intensity configuration."""
        settings = SustainabilitySettings(
            default_carbon_intensity_gco2_per_kwh=Decimal("200"),
            default_region="us-west",
        )
        assert settings.default_carbon_intensity_gco2_per_kwh == Decimal("200")
        assert settings.default_region == "us-west"

    def test_custom_api_configuration(self) -> None:
        """Test custom API configuration."""
        settings = SustainabilitySettings(
            carbon_intensity_api_url="https://custom-api.example.com",
            carbon_intensity_api_key="my-api-key",
            carbon_intensity_timeout_seconds=30,
        )
        assert settings.carbon_intensity_api_url == "https://custom-api.example.com"
        assert settings.carbon_intensity_api_key == "my-api-key"
        assert settings.carbon_intensity_timeout_seconds == 30

    def test_custom_prometheus_configuration(self) -> None:
        """Test custom Prometheus configuration."""
        settings = SustainabilitySettings(
            prometheus_url="http://prometheus.monitoring:9090",
            prometheus_timeout_seconds=60,
        )
        assert settings.prometheus_url == "http://prometheus.monitoring:9090"
        assert settings.prometheus_timeout_seconds == 60

    def test_custom_circuit_breaker_configuration(self) -> None:
        """Test custom circuit breaker configuration."""
        settings = SustainabilitySettings(
            circuit_breaker_failure_threshold=10,
            circuit_breaker_recovery_timeout=120,
        )
        assert settings.circuit_breaker_failure_threshold == 10
        assert settings.circuit_breaker_recovery_timeout == 120

    def test_custom_kepler_configuration(self) -> None:
        """Test custom Kepler configuration."""
        settings = SustainabilitySettings(
            kepler_namespace="monitoring",
            kepler_metrics_port=9103,
        )
        assert settings.kepler_namespace == "monitoring"
        assert settings.kepler_metrics_port == 9103

    def test_get_sustainability_settings(self) -> None:
        """Test get_sustainability_settings factory function."""
        settings = get_sustainability_settings()
        assert isinstance(settings, SustainabilitySettings)
        assert settings.currency == "USD"

    def test_env_prefix(self) -> None:
        """Test that env_prefix is configured correctly."""
        assert SustainabilitySettings.model_config["env_prefix"] == "SUSTAINABILITY_"
