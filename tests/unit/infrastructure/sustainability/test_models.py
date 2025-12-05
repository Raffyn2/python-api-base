"""Unit tests for sustainability data models."""

from datetime import datetime
from decimal import Decimal

import pytest

from src.infrastructure.sustainability.models import (
    AlertRule,
    AlertThreshold,
    CarbonIntensity,
    CarbonMetric,
    EnergyCost,
    EnergyEfficiency,
    EnergyMetric,
    SustainabilityReport,
)


class TestEnergyMetric:
    """Tests for EnergyMetric model."""

    def test_create_valid_metric(self):
        """Test creating a valid energy metric."""
        metric = EnergyMetric(
            namespace="default",
            pod="my-pod",
            container="app",
            energy_joules=Decimal("3600000"),
            timestamp=datetime.now(),
            source="rapl",
        )
        assert metric.namespace == "default"
        assert metric.energy_kwh == Decimal("1")

    def test_negative_energy_raises_error(self):
        """Test that negative energy raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            EnergyMetric(
                namespace="default",
                pod="my-pod",
                container="app",
                energy_joules=Decimal("-1"),
                timestamp=datetime.now(),
                source="rapl",
            )

    def test_energy_conversion(self):
        """Test energy unit conversions."""
        metric = EnergyMetric(
            namespace="default",
            pod="my-pod",
            container="app",
            energy_joules=Decimal("7200000"),
            timestamp=datetime.now(),
            source="rapl",
        )
        assert metric.energy_kwh == Decimal("2")
        assert metric.energy_wh == Decimal("2000")


class TestCarbonMetric:
    """Tests for CarbonMetric model."""

    def test_calculate_from_energy(self):
        """Test calculating carbon metric from energy."""
        energy = EnergyMetric(
            namespace="default",
            pod="my-pod",
            container="app",
            energy_joules=Decimal("3600000"),  # 1 kWh
            timestamp=datetime.now(),
            source="rapl",
        )
        intensity = CarbonIntensity(
            region="US",
            intensity_gco2_per_kwh=Decimal("400"),
            timestamp=datetime.now(),
            source="default",
        )
        
        metric = CarbonMetric.calculate(energy, intensity)
        
        assert metric.emissions_gco2 == Decimal("400")
        assert metric.confidence_lower == Decimal("360")
        assert metric.confidence_upper == Decimal("440")


class TestSustainabilityReport:
    """Tests for SustainabilityReport model."""

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        report = SustainabilityReport(
            namespace="default",
            period_start=datetime.now(),
            period_end=datetime.now(),
            total_energy_kwh=Decimal("100"),
            total_emissions_gco2=Decimal("30000"),
            total_cost=Decimal("12"),
            currency="USD",
            baseline_emissions_gco2=Decimal("50000"),
            target_emissions_gco2=Decimal("25000"),
        )
        
        # Progress = (50000 - 30000) / (50000 - 25000) * 100 = 80%
        assert report.progress_percentage == Decimal("80")

    def test_progress_none_without_baseline(self):
        """Test progress is None without baseline."""
        report = SustainabilityReport(
            namespace="default",
            period_start=datetime.now(),
            period_end=datetime.now(),
            total_energy_kwh=Decimal("100"),
            total_emissions_gco2=Decimal("30000"),
            total_cost=Decimal("12"),
            currency="USD",
        )
        
        assert report.progress_percentage is None


class TestAlertThreshold:
    """Tests for AlertThreshold model."""

    def test_valid_severity(self):
        """Test valid severity values."""
        threshold = AlertThreshold(
            namespace="default",
            deployment=None,
            energy_threshold_kwh=Decimal("100"),
            carbon_threshold_gco2=Decimal("40000"),
            cost_threshold=Decimal("12"),
            severity="warning",
        )
        assert threshold.severity == "warning"

    def test_invalid_severity_raises_error(self):
        """Test invalid severity raises ValueError."""
        with pytest.raises(ValueError, match="severity"):
            AlertThreshold(
                namespace="default",
                deployment=None,
                energy_threshold_kwh=Decimal("100"),
                carbon_threshold_gco2=Decimal("40000"),
                cost_threshold=Decimal("12"),
                severity="invalid",
            )


class TestAlertRule:
    """Tests for AlertRule model."""

    def test_to_prometheus_format(self):
        """Test conversion to Prometheus format."""
        rule = AlertRule(
            name="test_alert",
            expr="sum(rate(metric[5m])) > 100",
            duration="5m",
            severity="warning",
            annotations={"summary": "Test alert"},
            labels={"team": "platform"},
        )
        
        prometheus_format = rule.to_prometheus_format()
        
        assert prometheus_format["alert"] == "test_alert"
        assert prometheus_format["expr"] == "sum(rate(metric[5m])) > 100"
        assert prometheus_format["for"] == "5m"
        assert prometheus_format["labels"]["severity"] == "warning"
        assert prometheus_format["labels"]["team"] == "platform"
