"""Tests for sustainability data models.

Tests EnergyMetric, CarbonIntensity, CarbonMetric, and related models.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from infrastructure.sustainability.models import (
    GRAMS_PER_KG,
    JOULES_PER_KWH,
    KG_PER_TON,
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

    def test_joules(self) -> None:
        assert EnergyUnit.JOULES.value == "J"

    def test_kilowatt_hours(self) -> None:
        assert EnergyUnit.KILOWATT_HOURS.value == "kWh"

    def test_watt_hours(self) -> None:
        assert EnergyUnit.WATT_HOURS.value == "Wh"


class TestCarbonUnit:
    """Tests for CarbonUnit enum."""

    def test_grams_co2(self) -> None:
        assert CarbonUnit.GRAMS_CO2.value == "gCO2"

    def test_kilograms_co2(self) -> None:
        assert CarbonUnit.KILOGRAMS_CO2.value == "kgCO2"

    def test_tons_co2(self) -> None:
        assert CarbonUnit.TONS_CO2.value == "tCO2"


class TestConstants:
    """Tests for conversion constants."""

    def test_joules_per_kwh(self) -> None:
        assert Decimal(3600000) == JOULES_PER_KWH

    def test_grams_per_kg(self) -> None:
        assert Decimal(1000) == GRAMS_PER_KG

    def test_kg_per_ton(self) -> None:
        assert Decimal(1000) == KG_PER_TON


class TestEnergyMetric:
    """Tests for EnergyMetric dataclass."""

    @pytest.fixture()
    def sample_metric(self) -> EnergyMetric:
        return EnergyMetric(
            namespace="default",
            pod="app-pod-1",
            container="app",
            energy_joules=Decimal(3600000),  # 1 kWh
            timestamp=datetime.now(UTC),
            source="rapl",
        )

    def test_create_metric(self, sample_metric: EnergyMetric) -> None:
        assert sample_metric.namespace == "default"
        assert sample_metric.pod == "app-pod-1"
        assert sample_metric.container == "app"
        assert sample_metric.source == "rapl"

    def test_energy_kwh_conversion(self, sample_metric: EnergyMetric) -> None:
        assert sample_metric.energy_kwh == Decimal(1)

    def test_energy_wh_conversion(self, sample_metric: EnergyMetric) -> None:
        assert sample_metric.energy_wh == Decimal(1000)

    def test_negative_energy_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            EnergyMetric(
                namespace="default",
                pod="pod",
                container="container",
                energy_joules=Decimal(-100),
                timestamp=datetime.now(UTC),
                source="rapl",
            )

    def test_is_frozen(self, sample_metric: EnergyMetric) -> None:
        with pytest.raises(AttributeError):
            sample_metric.namespace = "changed"  # type: ignore


class TestCarbonIntensity:
    """Tests for CarbonIntensity dataclass."""

    def test_create_intensity(self) -> None:
        intensity = CarbonIntensity(
            region="us-west",
            intensity_gco2_per_kwh=Decimal(200),
            timestamp=datetime.now(UTC),
            source="electricitymap",
        )
        assert intensity.region == "us-west"
        assert intensity.intensity_gco2_per_kwh == Decimal(200)
        assert intensity.is_default is False

    def test_default_intensity(self) -> None:
        intensity = CarbonIntensity(
            region="global",
            intensity_gco2_per_kwh=Decimal(400),
            timestamp=datetime.now(UTC),
            source="default",
            is_default=True,
        )
        assert intensity.is_default is True

    def test_negative_intensity_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            CarbonIntensity(
                region="test",
                intensity_gco2_per_kwh=Decimal(-100),
                timestamp=datetime.now(UTC),
                source="test",
            )


class TestCarbonMetric:
    """Tests for CarbonMetric dataclass."""

    @pytest.fixture()
    def sample_intensity(self) -> CarbonIntensity:
        return CarbonIntensity(
            region="us-west",
            intensity_gco2_per_kwh=Decimal(200),
            timestamp=datetime.now(UTC),
            source="electricitymap",
        )

    @pytest.fixture()
    def sample_energy(self) -> EnergyMetric:
        return EnergyMetric(
            namespace="default",
            pod="app-pod-1",
            container="app",
            energy_joules=Decimal(3600000),  # 1 kWh
            timestamp=datetime.now(UTC),
            source="rapl",
        )

    def test_calculate_from_energy(self, sample_energy: EnergyMetric, sample_intensity: CarbonIntensity) -> None:
        metric = CarbonMetric.calculate(sample_energy, sample_intensity)

        assert metric.namespace == "default"
        assert metric.energy_kwh == Decimal(1)
        assert metric.emissions_gco2 == Decimal(200)  # 1 kWh * 200 gCO2/kWh

    def test_emissions_kgco2_conversion(self, sample_energy: EnergyMetric, sample_intensity: CarbonIntensity) -> None:
        metric = CarbonMetric.calculate(sample_energy, sample_intensity)
        assert metric.emissions_kgco2 == Decimal("0.2")

    def test_emissions_tco2_conversion(self, sample_energy: EnergyMetric, sample_intensity: CarbonIntensity) -> None:
        metric = CarbonMetric.calculate(sample_energy, sample_intensity)
        assert metric.emissions_tco2 == Decimal("0.0002")

    def test_confidence_bounds(self, sample_energy: EnergyMetric, sample_intensity: CarbonIntensity) -> None:
        metric = CarbonMetric.calculate(sample_energy, sample_intensity, confidence_margin=Decimal("0.1"))

        assert metric.confidence_lower == Decimal(180)  # 200 * 0.9
        assert metric.confidence_upper == Decimal(220)  # 200 * 1.1

    def test_negative_emissions_raises(self, sample_intensity: CarbonIntensity) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            CarbonMetric(
                namespace="default",
                pod="pod",
                container="container",
                energy_kwh=Decimal(1),
                carbon_intensity=sample_intensity,
                emissions_gco2=Decimal(-100),
                timestamp=datetime.now(UTC),
                confidence_lower=Decimal(0),
                confidence_upper=Decimal(100),
            )

    def test_invalid_confidence_lower_raises(self, sample_intensity: CarbonIntensity) -> None:
        with pytest.raises(ValueError, match="confidence_lower"):
            CarbonMetric(
                namespace="default",
                pod="pod",
                container="container",
                energy_kwh=Decimal(1),
                carbon_intensity=sample_intensity,
                emissions_gco2=Decimal(100),
                timestamp=datetime.now(UTC),
                confidence_lower=Decimal(150),  # Greater than emissions
                confidence_upper=Decimal(200),
            )

    def test_invalid_confidence_upper_raises(self, sample_intensity: CarbonIntensity) -> None:
        with pytest.raises(ValueError, match="confidence_upper"):
            CarbonMetric(
                namespace="default",
                pod="pod",
                container="container",
                energy_kwh=Decimal(1),
                carbon_intensity=sample_intensity,
                emissions_gco2=Decimal(100),
                timestamp=datetime.now(UTC),
                confidence_lower=Decimal(50),
                confidence_upper=Decimal(80),  # Less than emissions
            )


class TestEnergyCost:
    """Tests for EnergyCost dataclass."""

    def test_calculate_cost(self) -> None:
        now = datetime.now(UTC)
        cost = EnergyCost.calculate(
            energy_kwh=Decimal(100),
            price_per_kwh=Decimal("0.12"),
            currency="USD",
            period_start=now - timedelta(hours=1),
            period_end=now,
        )

        assert cost.energy_kwh == Decimal(100)
        assert cost.total_cost == Decimal(12)  # 100 * 0.12
        assert cost.currency == "USD"

    def test_negative_energy_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValueError, match="non-negative"):
            EnergyCost(
                energy_kwh=Decimal(-100),
                price_per_kwh=Decimal("0.12"),
                total_cost=Decimal(-12),
                currency="USD",
                period_start=now - timedelta(hours=1),
                period_end=now,
            )

    def test_negative_price_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValueError, match="non-negative"):
            EnergyCost(
                energy_kwh=Decimal(100),
                price_per_kwh=Decimal("-0.12"),
                total_cost=Decimal(-12),
                currency="USD",
                period_start=now - timedelta(hours=1),
                period_end=now,
            )


class TestSustainabilityReport:
    """Tests for SustainabilityReport dataclass."""

    @pytest.fixture()
    def sample_report(self) -> SustainabilityReport:
        now = datetime.now(UTC)
        return SustainabilityReport(
            namespace="production",
            period_start=now - timedelta(days=30),
            period_end=now,
            total_energy_kwh=Decimal(1000),
            total_emissions_gco2=Decimal(400000),
            total_cost=Decimal(120),
            currency="USD",
            baseline_emissions_gco2=Decimal(500000),
            target_emissions_gco2=Decimal(300000),
        )

    def test_progress_percentage(self, sample_report: SustainabilityReport) -> None:
        # Reduction: 500000 - 400000 = 100000
        # Target reduction: 500000 - 300000 = 200000
        # Progress: 100000 / 200000 * 100 = 50%
        assert sample_report.progress_percentage == Decimal(50)

    def test_reduction_percentage(self, sample_report: SustainabilityReport) -> None:
        # Reduction: 500000 - 400000 = 100000
        # Percentage: 100000 / 500000 * 100 = 20%
        assert sample_report.reduction_percentage == Decimal(20)

    def test_progress_none_without_baseline(self) -> None:
        now = datetime.now(UTC)
        report = SustainabilityReport(
            namespace="production",
            period_start=now - timedelta(days=30),
            period_end=now,
            total_energy_kwh=Decimal(1000),
            total_emissions_gco2=Decimal(400000),
            total_cost=Decimal(120),
            currency="USD",
        )
        assert report.progress_percentage is None
        assert report.reduction_percentage is None


class TestEnergyEfficiency:
    """Tests for EnergyEfficiency dataclass."""

    @pytest.fixture()
    def sample_efficiency(self) -> EnergyEfficiency:
        now = datetime.now(UTC)
        return EnergyEfficiency(
            namespace="default",
            deployment="api",
            total_energy_joules=Decimal(3600000),
            requests_count=1000,
            transactions_count=500,
            period_start=now - timedelta(hours=1),
            period_end=now,
        )

    def test_energy_per_request(self, sample_efficiency: EnergyEfficiency) -> None:
        # 3600000 J / 1000 requests = 3600 J/request
        assert sample_efficiency.energy_per_request_joules == Decimal(3600)

    def test_energy_per_transaction(self, sample_efficiency: EnergyEfficiency) -> None:
        # 3600000 J / 500 transactions = 7200 J/transaction
        assert sample_efficiency.energy_per_transaction_joules == Decimal(7200)

    def test_energy_per_request_zero_requests(self) -> None:
        now = datetime.now(UTC)
        efficiency = EnergyEfficiency(
            namespace="default",
            deployment="api",
            total_energy_joules=Decimal(3600000),
            requests_count=0,
            transactions_count=0,
            period_start=now - timedelta(hours=1),
            period_end=now,
        )
        assert efficiency.energy_per_request_joules is None
        assert efficiency.energy_per_transaction_joules is None

    def test_negative_requests_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValueError, match="non-negative"):
            EnergyEfficiency(
                namespace="default",
                deployment="api",
                total_energy_joules=Decimal(3600000),
                requests_count=-1,
                transactions_count=0,
                period_start=now - timedelta(hours=1),
                period_end=now,
            )


class TestAlertThreshold:
    """Tests for AlertThreshold dataclass."""

    def test_create_threshold(self) -> None:
        threshold = AlertThreshold(
            namespace="production",
            deployment="api",
            energy_threshold_kwh=Decimal(100),
            carbon_threshold_gco2=Decimal(40000),
            cost_threshold=Decimal(12),
        )
        assert threshold.namespace == "production"
        assert threshold.severity == "warning"

    def test_critical_severity(self) -> None:
        threshold = AlertThreshold(
            namespace="production",
            deployment=None,
            energy_threshold_kwh=Decimal(200),
            carbon_threshold_gco2=Decimal(80000),
            cost_threshold=Decimal(24),
            severity="critical",
        )
        assert threshold.severity == "critical"

    def test_invalid_severity_raises(self) -> None:
        with pytest.raises(ValueError, match="severity"):
            AlertThreshold(
                namespace="production",
                deployment=None,
                energy_threshold_kwh=Decimal(100),
                carbon_threshold_gco2=Decimal(40000),
                cost_threshold=Decimal(12),
                severity="invalid",
            )


class TestAlertRule:
    """Tests for AlertRule dataclass."""

    def test_create_rule(self) -> None:
        rule = AlertRule(
            name="HighEnergyConsumption",
            expr="energy_consumption_kwh > 100",
            duration="5m",
            severity="warning",
        )
        assert rule.name == "HighEnergyConsumption"
        assert rule.duration == "5m"

    def test_to_prometheus_format(self) -> None:
        rule = AlertRule(
            name="HighEnergyConsumption",
            expr="energy_consumption_kwh > 100",
            duration="5m",
            severity="warning",
            annotations={"summary": "High energy consumption detected"},
            labels={"team": "platform"},
        )

        prometheus_rule = rule.to_prometheus_format()

        assert prometheus_rule["alert"] == "HighEnergyConsumption"
        assert prometheus_rule["expr"] == "energy_consumption_kwh > 100"
        assert prometheus_rule["for"] == "5m"
        assert prometheus_rule["labels"]["severity"] == "warning"
        assert prometheus_rule["labels"]["team"] == "platform"
        assert prometheus_rule["annotations"]["summary"] == "High energy consumption detected"
