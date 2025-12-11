"""Tests for sustainability calculator module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from decimal import Decimal

import pytest

from infrastructure.sustainability.calculator import (
    aggregate_emissions,
    calculate_cost,
    calculate_efficiency,
    calculate_emissions,
    calculate_progress,
    calculate_savings,
    calculate_trend,
)
from infrastructure.sustainability.models import CarbonMetric


class TestCalculateEmissions:
    """Tests for calculate_emissions function."""

    def test_basic_calculation(self) -> None:
        """Test basic emissions calculation."""
        result = calculate_emissions(
            energy_kwh=Decimal(100),
            intensity_gco2_per_kwh=Decimal(400),
        )
        assert result == Decimal(40000)

    def test_zero_energy(self) -> None:
        """Test with zero energy consumption."""
        result = calculate_emissions(
            energy_kwh=Decimal(0),
            intensity_gco2_per_kwh=Decimal(400),
        )
        assert result == Decimal(0)

    def test_zero_intensity(self) -> None:
        """Test with zero carbon intensity."""
        result = calculate_emissions(
            energy_kwh=Decimal(100),
            intensity_gco2_per_kwh=Decimal(0),
        )
        assert result == Decimal(0)

    def test_negative_energy_raises(self) -> None:
        """Test that negative energy raises ValueError."""
        with pytest.raises(ValueError, match="energy_kwh must be non-negative"):
            calculate_emissions(
                energy_kwh=Decimal(-10),
                intensity_gco2_per_kwh=Decimal(400),
            )

    def test_negative_intensity_raises(self) -> None:
        """Test that negative intensity raises ValueError."""
        with pytest.raises(ValueError, match="intensity_gco2_per_kwh must be non-negative"):
            calculate_emissions(
                energy_kwh=Decimal(100),
                intensity_gco2_per_kwh=Decimal(-50),
            )

    def test_decimal_precision(self) -> None:
        """Test decimal precision is maintained."""
        result = calculate_emissions(
            energy_kwh=Decimal("1.5"),
            intensity_gco2_per_kwh=Decimal("0.3"),
        )
        assert result == Decimal("0.45")


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_basic_calculation(self) -> None:
        """Test basic cost calculation."""
        result = calculate_cost(
            energy_kwh=Decimal(100),
            price_per_kwh=Decimal("0.12"),
        )
        assert result == Decimal("12.00")

    def test_zero_energy(self) -> None:
        """Test with zero energy consumption."""
        result = calculate_cost(
            energy_kwh=Decimal(0),
            price_per_kwh=Decimal("0.12"),
        )
        assert result == Decimal(0)

    def test_negative_energy_raises(self) -> None:
        """Test that negative energy raises ValueError."""
        with pytest.raises(ValueError, match="energy_kwh must be non-negative"):
            calculate_cost(
                energy_kwh=Decimal(-10),
                price_per_kwh=Decimal("0.12"),
            )

    def test_negative_price_raises(self) -> None:
        """Test that negative price raises ValueError."""
        with pytest.raises(ValueError, match="price_per_kwh must be non-negative"):
            calculate_cost(
                energy_kwh=Decimal(100),
                price_per_kwh=Decimal("-0.12"),
            )


class TestAggregateEmissions:
    """Tests for aggregate_emissions function."""

    def test_aggregate_by_namespace(self) -> None:
        """Test aggregation by namespace."""
        from datetime import datetime

        from infrastructure.sustainability.models import CarbonIntensity

        intensity = CarbonIntensity(
            region="test",
            intensity_gco2_per_kwh=Decimal(400),
            timestamp=datetime.now(),
            source="test",
        )
        metrics = [
            CarbonMetric(
                namespace="ns1",
                pod="pod1",
                container="c1",
                energy_kwh=Decimal("0.25"),
                carbon_intensity=intensity,
                emissions_gco2=Decimal(100),
                timestamp=datetime.now(),
                confidence_lower=Decimal(90),
                confidence_upper=Decimal(110),
            ),
            CarbonMetric(
                namespace="ns1",
                pod="pod2",
                container="c2",
                energy_kwh=Decimal("0.5"),
                carbon_intensity=intensity,
                emissions_gco2=Decimal(200),
                timestamp=datetime.now(),
                confidence_lower=Decimal(180),
                confidence_upper=Decimal(220),
            ),
            CarbonMetric(
                namespace="ns2",
                pod="pod3",
                container="c3",
                energy_kwh=Decimal("0.375"),
                carbon_intensity=intensity,
                emissions_gco2=Decimal(150),
                timestamp=datetime.now(),
                confidence_lower=Decimal(135),
                confidence_upper=Decimal(165),
            ),
        ]
        result = aggregate_emissions(metrics, group_by="namespace")
        assert result["ns1"] == Decimal(300)
        assert result["ns2"] == Decimal(150)

    def test_aggregate_by_pod(self) -> None:
        """Test aggregation by pod."""
        from datetime import datetime

        from infrastructure.sustainability.models import CarbonIntensity

        intensity = CarbonIntensity(
            region="test",
            intensity_gco2_per_kwh=Decimal(400),
            timestamp=datetime.now(),
            source="test",
        )
        metrics = [
            CarbonMetric(
                namespace="ns1",
                pod="pod1",
                container="c1",
                energy_kwh=Decimal("0.25"),
                carbon_intensity=intensity,
                emissions_gco2=Decimal(100),
                timestamp=datetime.now(),
                confidence_lower=Decimal(90),
                confidence_upper=Decimal(110),
            ),
            CarbonMetric(
                namespace="ns1",
                pod="pod1",
                container="c2",
                energy_kwh=Decimal("0.125"),
                carbon_intensity=intensity,
                emissions_gco2=Decimal(50),
                timestamp=datetime.now(),
                confidence_lower=Decimal(45),
                confidence_upper=Decimal(55),
            ),
        ]
        result = aggregate_emissions(metrics, group_by="pod")
        assert result["pod1"] == Decimal(150)

    def test_empty_metrics(self) -> None:
        """Test with empty metrics list."""
        result = aggregate_emissions([], group_by="namespace")
        assert result == {}


class TestCalculateEfficiency:
    """Tests for calculate_efficiency function."""

    def test_basic_calculation(self) -> None:
        """Test basic efficiency calculation."""
        energy_per_request, energy_per_transaction = calculate_efficiency(
            total_energy_joules=Decimal(1000),
            requests_count=100,
            transactions_count=50,
        )
        assert energy_per_request == Decimal(10)
        assert energy_per_transaction == Decimal(20)

    def test_zero_requests(self) -> None:
        """Test with zero requests."""
        energy_per_request, energy_per_transaction = calculate_efficiency(
            total_energy_joules=Decimal(1000),
            requests_count=0,
            transactions_count=50,
        )
        assert energy_per_request is None
        assert energy_per_transaction == Decimal(20)

    def test_zero_transactions(self) -> None:
        """Test with zero transactions."""
        energy_per_request, energy_per_transaction = calculate_efficiency(
            total_energy_joules=Decimal(1000),
            requests_count=100,
            transactions_count=0,
        )
        assert energy_per_request == Decimal(10)
        assert energy_per_transaction is None

    def test_negative_energy_raises(self) -> None:
        """Test that negative energy raises ValueError."""
        with pytest.raises(ValueError, match="total_energy_joules must be non-negative"):
            calculate_efficiency(
                total_energy_joules=Decimal(-100),
                requests_count=10,
                transactions_count=5,
            )

    def test_negative_requests_raises(self) -> None:
        """Test that negative requests raises ValueError."""
        with pytest.raises(ValueError, match="requests_count must be non-negative"):
            calculate_efficiency(
                total_energy_joules=Decimal(100),
                requests_count=-10,
                transactions_count=5,
            )

    def test_negative_transactions_raises(self) -> None:
        """Test that negative transactions raises ValueError."""
        with pytest.raises(ValueError, match="transactions_count must be non-negative"):
            calculate_efficiency(
                total_energy_joules=Decimal(100),
                requests_count=10,
                transactions_count=-5,
            )


class TestCalculateProgress:
    """Tests for calculate_progress function."""

    def test_basic_progress(self) -> None:
        """Test basic progress calculation."""
        result = calculate_progress(
            baseline=Decimal(100),
            current=Decimal(80),
            target=Decimal(50),
        )
        # (100-80)/(100-50) * 100 = 20/50 * 100 = 40%
        assert result == Decimal(40)

    def test_target_achieved(self) -> None:
        """Test when target is achieved."""
        result = calculate_progress(
            baseline=Decimal(100),
            current=Decimal(50),
            target=Decimal(50),
        )
        assert result == Decimal(100)

    def test_target_exceeded(self) -> None:
        """Test when target is exceeded."""
        result = calculate_progress(
            baseline=Decimal(100),
            current=Decimal(30),
            target=Decimal(50),
        )
        # (100-30)/(100-50) * 100 = 70/50 * 100 = 140%
        assert result == Decimal(140)

    def test_no_reduction_target(self) -> None:
        """Test when baseline equals target."""
        result = calculate_progress(
            baseline=Decimal(100),
            current=Decimal(80),
            target=Decimal(100),
        )
        assert result is None

    def test_negative_values_raise(self) -> None:
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="All values must be non-negative"):
            calculate_progress(
                baseline=Decimal(-100),
                current=Decimal(80),
                target=Decimal(50),
            )


class TestCalculateSavings:
    """Tests for calculate_savings function."""

    def test_positive_savings(self) -> None:
        """Test positive savings calculation."""
        result = calculate_savings(
            baseline_cost=Decimal(1000),
            current_cost=Decimal(800),
        )
        assert result == Decimal(200)

    def test_negative_savings(self) -> None:
        """Test negative savings (cost increase)."""
        result = calculate_savings(
            baseline_cost=Decimal(800),
            current_cost=Decimal(1000),
        )
        assert result == Decimal(-200)

    def test_no_change(self) -> None:
        """Test no change in cost."""
        result = calculate_savings(
            baseline_cost=Decimal(1000),
            current_cost=Decimal(1000),
        )
        assert result == Decimal(0)

    def test_negative_baseline_raises(self) -> None:
        """Test that negative baseline raises ValueError."""
        with pytest.raises(ValueError, match="baseline_cost must be non-negative"):
            calculate_savings(
                baseline_cost=Decimal(-100),
                current_cost=Decimal(80),
            )

    def test_negative_current_raises(self) -> None:
        """Test that negative current raises ValueError."""
        with pytest.raises(ValueError, match="current_cost must be non-negative"):
            calculate_savings(
                baseline_cost=Decimal(100),
                current_cost=Decimal(-80),
            )


class TestCalculateTrend:
    """Tests for calculate_trend function."""

    def test_positive_trend(self) -> None:
        """Test positive trend (increase)."""
        result = calculate_trend(
            previous=Decimal(100),
            current=Decimal(120),
        )
        assert result == Decimal(20)

    def test_negative_trend(self) -> None:
        """Test negative trend (decrease)."""
        result = calculate_trend(
            previous=Decimal(100),
            current=Decimal(80),
        )
        assert result == Decimal(-20)

    def test_no_change(self) -> None:
        """Test no change."""
        result = calculate_trend(
            previous=Decimal(100),
            current=Decimal(100),
        )
        assert result == Decimal(0)

    def test_zero_previous(self) -> None:
        """Test with zero previous value."""
        result = calculate_trend(
            previous=Decimal(0),
            current=Decimal(100),
        )
        assert result is None

    def test_negative_values_raise(self) -> None:
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="Values must be non-negative"):
            calculate_trend(
                previous=Decimal(-100),
                current=Decimal(80),
            )
