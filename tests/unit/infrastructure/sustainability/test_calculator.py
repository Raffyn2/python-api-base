"""Unit tests for sustainability calculator module."""

from decimal import Decimal

import pytest

from src.infrastructure.sustainability.calculator import (
    calculate_cost,
    calculate_efficiency,
    calculate_emissions,
    calculate_progress,
    calculate_savings,
    calculate_trend,
)


class TestCalculateEmissions:
    """Tests for calculate_emissions function."""

    def test_basic_calculation(self):
        """Test basic emission calculation."""
        result = calculate_emissions(Decimal("10"), Decimal("400"))
        assert result == Decimal("4000")

    def test_zero_energy(self):
        """Test with zero energy."""
        result = calculate_emissions(Decimal("0"), Decimal("400"))
        assert result == Decimal("0")

    def test_negative_energy_raises_error(self):
        """Test negative energy raises ValueError."""
        with pytest.raises(ValueError):
            calculate_emissions(Decimal("-1"), Decimal("400"))


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_basic_calculation(self):
        """Test basic cost calculation."""
        result = calculate_cost(Decimal("100"), Decimal("0.12"))
        assert result == Decimal("12.00")

    def test_zero_energy(self):
        """Test with zero energy."""
        result = calculate_cost(Decimal("0"), Decimal("0.12"))
        assert result == Decimal("0")


class TestCalculateEfficiency:
    """Tests for calculate_efficiency function."""

    def test_basic_calculation(self):
        """Test basic efficiency calculation."""
        per_request, per_transaction = calculate_efficiency(
            Decimal("1000"), 100, 50
        )
        assert per_request == Decimal("10")
        assert per_transaction == Decimal("20")

    def test_zero_requests(self):
        """Test with zero requests."""
        per_request, per_transaction = calculate_efficiency(
            Decimal("1000"), 0, 50
        )
        assert per_request is None
        assert per_transaction == Decimal("20")


class TestCalculateProgress:
    """Tests for calculate_progress function."""

    def test_50_percent_progress(self):
        """Test 50% progress calculation."""
        result = calculate_progress(
            baseline=Decimal("100"),
            current=Decimal("75"),
            target=Decimal("50"),
        )
        assert result == Decimal("50")

    def test_100_percent_progress(self):
        """Test 100% progress (target reached)."""
        result = calculate_progress(
            baseline=Decimal("100"),
            current=Decimal("50"),
            target=Decimal("50"),
        )
        assert result == Decimal("100")

    def test_exceeded_target(self):
        """Test progress exceeding target."""
        result = calculate_progress(
            baseline=Decimal("100"),
            current=Decimal("25"),
            target=Decimal("50"),
        )
        assert result == Decimal("150")


class TestCalculateSavings:
    """Tests for calculate_savings function."""

    def test_positive_savings(self):
        """Test positive savings."""
        result = calculate_savings(Decimal("100"), Decimal("80"))
        assert result == Decimal("20")

    def test_negative_savings(self):
        """Test negative savings (cost increase)."""
        result = calculate_savings(Decimal("100"), Decimal("120"))
        assert result == Decimal("-20")


class TestCalculateTrend:
    """Tests for calculate_trend function."""

    def test_positive_trend(self):
        """Test positive trend (increase)."""
        result = calculate_trend(Decimal("100"), Decimal("120"))
        assert result == Decimal("20")

    def test_negative_trend(self):
        """Test negative trend (decrease)."""
        result = calculate_trend(Decimal("100"), Decimal("80"))
        assert result == Decimal("-20")

    def test_zero_previous_returns_none(self):
        """Test zero previous value returns None."""
        result = calculate_trend(Decimal("0"), Decimal("100"))
        assert result is None
