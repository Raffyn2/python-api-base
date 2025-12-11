"""Unit tests for sustainability models.

Tests EnergyMetric, CarbonMetric, EnergyCost, and related models.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from infrastructure.sustainability.models import (
    AlertRule,
    AlertThreshold,
    CarbonIntensity,
    CarbonMetric,
    CarbonUnit,
    EnergyCost,
    EnergyEfficiency,
    EnergyMetric,
    EnergyUnit,
    SustainabilityReport,
)


class TestEnergyUnit:
    """Tests for EnergyUnit enum."""

    def test_joules_value(self) -> None:
        """Test JOULES value."""
        assert EnergyUnit.JOULES.value == "J"

    def test_kilowatt_hours_value(self) -> None:
        """Test KILOWATT_HOURS value."""
        assert EnergyUnit.KILOWATT_HOURS.value == "kWh"

    def test_watt_hours_value(self) -> None:
        """Test WATT_HOURS value."""
        assert EnergyUnit.WATT_HOURS.value == "Wh"


class TestCarbonUnit:
    """Tests for CarbonUnit enum."""

    def test_grams_co2_value(self) -> None:
        """Test GRAMS_CO2 value."""
        assert CarbonUnit.GRAMS_CO2.value == "gCO2"

    def test_kilograms_co2_value(self) -> None:
        """Test KILOGRAMS_CO2 value."""
        assert CarbonUnit.KILOGRAMS_CO2.value == "kgCO2"


class TestEnergyMetric:
    """Tests for EnergyMetric dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic energy metric creation."""
        metric = EnergyMetric(
            namespace="default",
            pod="app-pod-1",
            container="app",
            energy_joules=Decimal(3600000),
            timestamp=datetime.now(),
            source="rapl",
        )
        assert metric.namespace == "default"
        assert metric.pod == "app-pod-1"
        assert metric.energy_joules == Decimal(3600000)

    def test_energy_kwh_conversion(self) -> None:
        """Test energy conversion to kWh."""
        metric = EnergyMetric(
            namespace="default",
            pod="pod-1",
            container="app",
            energy_joules=Decimal(3600000),  # 1 kWh
            timestamp=datetime.now(),
            source="rapl",
        )
        assert metric.energy_kwh == Decimal(1)

    def test_energy_wh_conversion(self) -> None:
        """Test energy conversion to Wh."""
        metric = EnergyMetric(
            namespace="default",
            pod="pod-1",
            container="app",
            energy_joules=Decimal(3600),  # 1 Wh
            timestamp=datetime.now(),
            source="rapl",
        )
        assert metric.energy_wh == Decimal(1)

    def test_negative_energy_raises(self) -> None:
        """Test negative energy raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            EnergyMetric(
                namespace="default",
                pod="pod-1",
                container="app",
                energy_joules=Decimal(-100),
                timestamp=datetime.now(),
                source="rapl",
            )


class TestCarbonIntensity:
    """Tests for CarbonIntensity dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic carbon intensity creation."""
        intensity = CarbonIntensity(
            region="us-east-1",
            intensity_gco2_per_kwh=Decimal(400),
            timestamp=datetime.now(),
            source="electricitymap",
        )
        assert intensity.region == "us-east-1"
        assert intensity.intensity_gco2_per_kwh == Decimal(400)
        assert intensity.is_default is False

    def test_default_intensity(self) -> None:
        """Test default intensity flag."""
        intensity = CarbonIntensity(
            region="global",
            intensity_gco2_per_kwh=Decimal(500),
            timestamp=datetime.now(),
            source="default",
            is_default=True,
        )
        assert intensity.is_default is True

    def test_negative_intensity_raises(self) -> None:
        """Test negative intensity raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            CarbonIntensity(
                region="test",
                intensity_gco2_per_kwh=Decimal(-100),
                timestamp=datetime.now(),
                source="test",
            )


class TestCarbonMetric:
    """Tests for CarbonMetric dataclass."""

    @pytest.fixture()
    def energy_metric(self) -> EnergyMetric:
        """Create test energy metric."""
        return EnergyMetric(
            namespace="default",
            pod="pod-1",
            container="app",
            energy_joules=Decimal(3600000),  # 1 kWh
            timestamp=datetime.now(),
            source="rapl",
        )

    @pytest.fixture()
    def carbon_intensity(self) -> CarbonIntensity:
        """Create test carbon intensity."""
        return CarbonIntensity(
            region="us-east-1",
            intensity_gco2_per_kwh=Decimal(400),
            timestamp=datetime.now(),
            source="electricitymap",
        )

    def test_calculate_emissions(self, energy_metric: EnergyMetric, carbon_intensity: CarbonIntensity) -> None:
        """Test calculating carbon emissions."""
        metric = CarbonMetric.calculate(energy_metric, carbon_intensity)
        assert metric.emissions_gco2 == Decimal(400)  # 1 kWh * 400 gCO2/kWh

    def test_emissions_kgco2(self, energy_metric: EnergyMetric, carbon_intensity: CarbonIntensity) -> None:
        """Test emissions conversion to kgCO2."""
        metric = CarbonMetric.calculate(energy_metric, carbon_intensity)
        assert metric.emissions_kgco2 == Decimal("0.4")

    def test_confidence_interval(self, energy_metric: EnergyMetric, carbon_intensity: CarbonIntensity) -> None:
        """Test confidence interval calculation."""
        metric = CarbonMetric.calculate(energy_metric, carbon_intensity, confidence_margin=Decimal("0.1"))
        assert metric.confidence_lower == Decimal(360)  # 400 * 0.9
        assert metric.confidence_upper == Decimal(440)  # 400 * 1.1


class TestEnergyCost:
    """Tests for EnergyCost dataclass."""

    def test_calculate_cost(self) -> None:
        """Test calculating energy cost."""
        now = datetime.now()
        cost = EnergyCost.calculate(
            energy_kwh=Decimal(100),
            price_per_kwh=Decimal("0.12"),
            currency="USD",
            period_start=now,
            period_end=now,
        )
        assert cost.total_cost == Decimal("12.00")

    def test_negative_energy_raises(self) -> None:
        """Test negative energy raises ValueError."""
        now = datetime.now()
        with pytest.raises(ValueError, match="non-negative"):
            EnergyCost(
                energy_kwh=Decimal(-100),
                price_per_kwh=Decimal("0.12"),
                total_cost=Decimal(-12),
                currency="USD",
                period_start=now,
                period_end=now,
            )


class TestSustainabilityReport:
    """Tests for SustainabilityReport dataclass."""

    def test_progress_percentage(self) -> None:
        """Test progress percentage calculation."""
        now = datetime.now()
        report = SustainabilityReport(
            namespace="default",
            period_start=now,
            period_end=now,
            total_energy_kwh=Decimal(100),
            total_emissions_gco2=Decimal(300),  # Reduced from 400 to 300
            total_cost=Decimal(12),
            currency="USD",
            baseline_emissions_gco2=Decimal(400),
            target_emissions_gco2=Decimal(200),  # Target: reduce by 200
        )
        # Progress: (400-300)/(400-200) = 100/200 = 50%
        assert report.progress_percentage == Decimal(50)

    def test_reduction_percentage(self) -> None:
        """Test reduction percentage calculation."""
        now = datetime.now()
        report = SustainabilityReport(
            namespace="default",
            period_start=now,
            period_end=now,
            total_energy_kwh=Decimal(100),
            total_emissions_gco2=Decimal(300),
            total_cost=Decimal(12),
            currency="USD",
            baseline_emissions_gco2=Decimal(400),
        )
        # Reduction: (400-300)/400 = 25%
        assert report.reduction_percentage == Decimal(25)

    def test_no_baseline_returns_none(self) -> None:
        """Test no baseline returns None for percentages."""
        now = datetime.now()
        report = SustainabilityReport(
            namespace="default",
            period_start=now,
            period_end=now,
            total_energy_kwh=Decimal(100),
            total_emissions_gco2=Decimal(300),
            total_cost=Decimal(12),
            currency="USD",
        )
        assert report.progress_percentage is None
        assert report.reduction_percentage is None


class TestEnergyEfficiency:
    """Tests for EnergyEfficiency dataclass."""

    def test_energy_per_request(self) -> None:
        """Test energy per request calculation."""
        now = datetime.now()
        efficiency = EnergyEfficiency(
            namespace="default",
            deployment="app",
            total_energy_joules=Decimal(1000),
            requests_count=100,
            transactions_count=50,
            period_start=now,
            period_end=now,
        )
        assert efficiency.energy_per_request_joules == Decimal(10)

    def test_energy_per_transaction(self) -> None:
        """Test energy per transaction calculation."""
        now = datetime.now()
        efficiency = EnergyEfficiency(
            namespace="default",
            deployment="app",
            total_energy_joules=Decimal(1000),
            requests_count=100,
            transactions_count=50,
            period_start=now,
            period_end=now,
        )
        assert efficiency.energy_per_transaction_joules == Decimal(20)

    def test_zero_requests_returns_none(self) -> None:
        """Test zero requests returns None."""
        now = datetime.now()
        efficiency = EnergyEfficiency(
            namespace="default",
            deployment="app",
            total_energy_joules=Decimal(1000),
            requests_count=0,
            transactions_count=0,
            period_start=now,
            period_end=now,
        )
        assert efficiency.energy_per_request_joules is None
        assert efficiency.energy_per_transaction_joules is None


class TestAlertThreshold:
    """Tests for AlertThreshold dataclass."""

    def test_valid_severity(self) -> None:
        """Test valid severity values."""
        threshold = AlertThreshold(
            namespace="default",
            deployment=None,
            energy_threshold_kwh=Decimal(100),
            carbon_threshold_gco2=Decimal(40000),
            cost_threshold=Decimal(12),
            severity="warning",
        )
        assert threshold.severity == "warning"

    def test_invalid_severity_raises(self) -> None:
        """Test invalid severity raises ValueError."""
        with pytest.raises(ValueError, match="severity must be"):
            AlertThreshold(
                namespace="default",
                deployment=None,
                energy_threshold_kwh=Decimal(100),
                carbon_threshold_gco2=Decimal(40000),
                cost_threshold=Decimal(12),
                severity="info",
            )


class TestAlertRule:
    """Tests for AlertRule dataclass."""

    def test_to_prometheus_format(self) -> None:
        """Test conversion to Prometheus format."""
        rule = AlertRule(
            name="HighEnergyConsumption",
            expr="energy_kwh > 100",
            duration="5m",
            severity="warning",
            annotations={"summary": "High energy consumption"},
        )
        prometheus_format = rule.to_prometheus_format()
        assert prometheus_format["alert"] == "HighEnergyConsumption"
        assert prometheus_format["expr"] == "energy_kwh > 100"
        assert prometheus_format["for"] == "5m"
        assert prometheus_format["labels"]["severity"] == "warning"
