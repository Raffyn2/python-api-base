"""Unit tests for sustainability modules.

**Feature: test-coverage-80-percent-v3**
"""

from decimal import Decimal

import pytest

from infrastructure.sustainability.calculator import (
    calculate_cost,
    calculate_efficiency,
    calculate_emissions,
    calculate_progress,
    calculate_savings,
    calculate_trend,
)


class TestCalculateEmissions:
    """Tests for calculate_emissions function."""

    def test_calculate_emissions_basic(self) -> None:
        """Test basic emissions calculation."""
        result = calculate_emissions(
            energy_kwh=Decimal(100),
            intensity_gco2_per_kwh=Decimal(500),
        )
        assert result == Decimal(50000)

    def test_calculate_emissions_zero_energy(self) -> None:
        """Test emissions with zero energy."""
        result = calculate_emissions(
            energy_kwh=Decimal(0),
            intensity_gco2_per_kwh=Decimal(500),
        )
        assert result == Decimal(0)

    def test_calculate_emissions_negative_energy_raises(self) -> None:
        """Test negative energy raises error."""
        with pytest.raises(ValueError, match="non-negative"):
            calculate_emissions(
                energy_kwh=Decimal(-10),
                intensity_gco2_per_kwh=Decimal(500),
            )


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_calculate_cost_basic(self) -> None:
        """Test basic cost calculation."""
        result = calculate_cost(
            energy_kwh=Decimal(100),
            price_per_kwh=Decimal("0.15"),
        )
        assert result == Decimal("15.00")

    def test_calculate_cost_zero_energy(self) -> None:
        """Test cost with zero energy."""
        result = calculate_cost(
            energy_kwh=Decimal(0),
            price_per_kwh=Decimal("0.15"),
        )
        assert result == Decimal(0)


class TestCalculateEfficiency:
    """Tests for calculate_efficiency function."""

    def test_calculate_efficiency_basic(self) -> None:
        """Test basic efficiency calculation."""
        per_request, per_transaction = calculate_efficiency(
            total_energy_joules=Decimal(1000),
            requests_count=100,
            transactions_count=50,
        )
        assert per_request == Decimal(10)
        assert per_transaction == Decimal(20)

    def test_calculate_efficiency_zero_counts(self) -> None:
        """Test efficiency with zero counts."""
        per_request, per_transaction = calculate_efficiency(
            total_energy_joules=Decimal(1000),
            requests_count=0,
            transactions_count=0,
        )
        assert per_request is None
        assert per_transaction is None


class TestCalculateProgress:
    """Tests for calculate_progress function."""

    def test_calculate_progress_basic(self) -> None:
        """Test basic progress calculation."""
        result = calculate_progress(
            baseline=Decimal(100),
            current=Decimal(50),
            target=Decimal(0),
        )
        assert result == Decimal(50)

    def test_calculate_progress_target_reached(self) -> None:
        """Test progress when target is reached."""
        result = calculate_progress(
            baseline=Decimal(100),
            current=Decimal(0),
            target=Decimal(0),
        )
        assert result == Decimal(100)

    def test_calculate_progress_no_reduction_needed(self) -> None:
        """Test progress when no reduction needed."""
        result = calculate_progress(
            baseline=Decimal(100),
            current=Decimal(50),
            target=Decimal(100),
        )
        assert result is None


class TestCalculateSavings:
    """Tests for calculate_savings function."""

    def test_calculate_savings_positive(self) -> None:
        """Test positive savings."""
        result = calculate_savings(
            baseline_cost=Decimal(1000),
            current_cost=Decimal(800),
        )
        assert result == Decimal(200)

    def test_calculate_savings_negative(self) -> None:
        """Test negative savings (cost increase)."""
        result = calculate_savings(
            baseline_cost=Decimal(800),
            current_cost=Decimal(1000),
        )
        assert result == Decimal(-200)


class TestCalculateTrend:
    """Tests for calculate_trend function."""

    def test_calculate_trend_increase(self) -> None:
        """Test trend with increase."""
        result = calculate_trend(
            previous=Decimal(100),
            current=Decimal(120),
        )
        assert result == Decimal(20)

    def test_calculate_trend_decrease(self) -> None:
        """Test trend with decrease."""
        result = calculate_trend(
            previous=Decimal(100),
            current=Decimal(80),
        )
        assert result == Decimal(-20)

    def test_calculate_trend_zero_previous(self) -> None:
        """Test trend with zero previous."""
        result = calculate_trend(
            previous=Decimal(0),
            current=Decimal(100),
        )
        assert result is None
