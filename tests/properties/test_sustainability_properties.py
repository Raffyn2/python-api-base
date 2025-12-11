"""
Property-based tests for sustainability module.

Uses Hypothesis to verify correctness properties across random inputs.
"""

import csv
import io
import json
from datetime import datetime
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st

from src.infrastructure.sustainability.alerts import generate_alert_rule
from src.infrastructure.sustainability.calculator import (
    aggregate_emissions,
    calculate_cost,
    calculate_efficiency,
    calculate_emissions,
    calculate_progress,
    calculate_savings,
    calculate_trend,
)
from src.infrastructure.sustainability.models import (
    AlertThreshold,
    CarbonIntensity,
    CarbonMetric,
    EnergyMetric,
)
from src.infrastructure.sustainability.serializer import (
    ValidationError,
    deserialize_carbon_metric,
    deserialize_carbon_metric_from_json,
    export_to_csv,
    export_to_json,
    serialize_carbon_metric,
    serialize_carbon_metric_to_json,
)

# Strategies for generating test data
decimal_positive = st.decimals(
    min_value=Decimal("0.001"),
    max_value=Decimal(1000000),
    allow_nan=False,
    allow_infinity=False,
    places=6,
)

decimal_non_negative = st.decimals(
    min_value=Decimal(0),
    max_value=Decimal(1000000),
    allow_nan=False,
    allow_infinity=False,
    places=6,
)

namespace_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-_"),
    min_size=1,
    max_size=63,
).filter(lambda x: x[0].isalpha())

pod_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-"),
    min_size=1,
    max_size=63,
).filter(lambda x: x[0].isalpha())


@st.composite
def energy_metric_strategy(draw):
    """Generate random EnergyMetric."""
    return EnergyMetric(
        namespace=draw(namespace_strategy),
        pod=draw(pod_strategy),
        container=draw(pod_strategy),
        energy_joules=draw(decimal_positive),
        timestamp=datetime.now(),
        source=draw(st.sampled_from(["rapl", "acpi", "model"])),
    )


@st.composite
def carbon_intensity_strategy(draw):
    """Generate random CarbonIntensity."""
    return CarbonIntensity(
        region=draw(st.text(min_size=2, max_size=10, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
        intensity_gco2_per_kwh=draw(decimal_positive),
        timestamp=datetime.now(),
        source=draw(st.sampled_from(["electricity-maps", "default", "manual"])),
        is_default=draw(st.booleans()),
    )


@st.composite
def carbon_metric_strategy(draw):
    """Generate random CarbonMetric."""
    energy = draw(energy_metric_strategy())
    intensity = draw(carbon_intensity_strategy())
    return CarbonMetric.calculate(energy, intensity)


class TestCarbonEmissionCalculation:
    """
    Property 2: Carbon Emission Calculation
    For any energy (kWh) and intensity (gCO2/kWh), emissions = energy × intensity.
    Validates: Requirements 3.1
    """

    @settings(max_examples=100)
    @given(energy=decimal_positive, intensity=decimal_positive)
    def test_emissions_equals_energy_times_intensity(self, energy: Decimal, intensity: Decimal):
        """Feature: kepler-greenops-sustainability, Property 2: Carbon Emission Calculation"""
        result = calculate_emissions(energy, intensity)
        expected = energy * intensity
        assert result == expected


class TestEnergyCostCalculation:
    """
    Property 3: Energy Cost Calculation
    For any energy (kWh) and price ($/kWh), cost = energy × price.
    Validates: Requirements 6.1
    """

    @settings(max_examples=100)
    @given(energy=decimal_positive, price=decimal_positive)
    def test_cost_equals_energy_times_price(self, energy: Decimal, price: Decimal):
        """Feature: kepler-greenops-sustainability, Property 3: Energy Cost Calculation"""
        result = calculate_cost(energy, price)
        expected = energy * price
        assert result == expected


class TestEmissionsAggregation:
    """
    Property 4: Emissions Aggregation Consistency
    Sum of individual emissions equals aggregated total.
    Validates: Requirements 3.3
    """

    @settings(max_examples=100)
    @given(metrics=st.lists(carbon_metric_strategy(), min_size=1, max_size=20))
    def test_aggregation_sum_equals_total(self, metrics: list[CarbonMetric]):
        """Feature: kepler-greenops-sustainability, Property 4: Emissions Aggregation Consistency"""
        aggregated = aggregate_emissions(metrics, "namespace")
        total_aggregated = sum(aggregated.values())
        total_individual = sum(m.emissions_gco2 for m in metrics)
        assert abs(total_aggregated - total_individual) < Decimal("0.000001")


class TestGoalProgressCalculation:
    """
    Property 5: Goal Progress Calculation
    progress = ((baseline - current) / (baseline - target)) × 100
    Validates: Requirements 3.5
    """

    @settings(max_examples=100)
    @given(
        baseline=decimal_positive,
        current=decimal_non_negative,
        target=decimal_non_negative,
    )
    def test_progress_calculation(self, baseline: Decimal, current: Decimal, target: Decimal):
        """Feature: kepler-greenops-sustainability, Property 5: Goal Progress Calculation"""
        if baseline == target:
            result = calculate_progress(baseline, current, target)
            assert result is None
        else:
            result = calculate_progress(baseline, current, target)
            expected = ((baseline - current) / (baseline - target)) * Decimal(100)
            assert result is not None
            assert abs(result - expected) < Decimal("0.000001")


class TestEnergyEfficiencyCalculation:
    """
    Property 6: Energy Efficiency Calculation
    For any energy and count > 0, efficiency = energy / count.
    Validates: Requirements 2.4
    """

    @settings(max_examples=100)
    @given(
        energy=decimal_positive,
        requests=st.integers(min_value=1, max_value=1000000),
        transactions=st.integers(min_value=1, max_value=1000000),
    )
    def test_efficiency_calculation(self, energy: Decimal, requests: int, transactions: int):
        """Feature: kepler-greenops-sustainability, Property 6: Energy Efficiency Calculation"""
        per_request, per_transaction = calculate_efficiency(energy, requests, transactions)

        assert per_request is not None
        assert per_transaction is not None
        assert per_request == energy / Decimal(requests)
        assert per_transaction == energy / Decimal(transactions)


class TestCostSavingsCalculation:
    """
    Property 7: Cost Savings Calculation
    savings = baseline_cost - current_cost
    Validates: Requirements 6.3
    """

    @settings(max_examples=100)
    @given(baseline=decimal_non_negative, current=decimal_non_negative)
    def test_savings_calculation(self, baseline: Decimal, current: Decimal):
        """Feature: kepler-greenops-sustainability, Property 7: Cost Savings Calculation"""
        result = calculate_savings(baseline, current)
        expected = baseline - current
        assert result == expected


class TestTrendCalculation:
    """
    Property 8: Trend Calculation
    trend = ((current - previous) / previous) × 100
    Validates: Requirements 6.4
    """

    @settings(max_examples=100)
    @given(previous=decimal_positive, current=decimal_non_negative)
    def test_trend_calculation(self, previous: Decimal, current: Decimal):
        """Feature: kepler-greenops-sustainability, Property 8: Trend Calculation"""
        result = calculate_trend(previous, current)
        expected = ((current - previous) / previous) * Decimal(100)
        assert result is not None
        assert abs(result - expected) < Decimal("0.000001")


class TestRoundTripSerialization:
    """
    Property 1: Carbon Metrics Round-Trip Serialization
    Serializing and deserializing produces equivalent object.
    Validates: Requirements 7.1, 7.2, 7.3
    """

    @settings(max_examples=100)
    @given(metric=carbon_metric_strategy())
    def test_round_trip_preserves_data(self, metric: CarbonMetric):
        """Feature: kepler-greenops-sustainability, Property 1: Carbon Metrics Round-Trip Serialization"""
        serialized = serialize_carbon_metric(metric)
        deserialized = deserialize_carbon_metric(serialized)

        assert deserialized.namespace == metric.namespace
        assert deserialized.pod == metric.pod
        assert deserialized.container == metric.container
        assert deserialized.energy_kwh == metric.energy_kwh
        assert deserialized.emissions_gco2 == metric.emissions_gco2
        assert deserialized.confidence_lower == metric.confidence_lower
        assert deserialized.confidence_upper == metric.confidence_upper

    @settings(max_examples=100)
    @given(metric=carbon_metric_strategy())
    def test_json_round_trip(self, metric: CarbonMetric):
        """Feature: kepler-greenops-sustainability, Property 1: JSON Round-Trip"""
        json_str = serialize_carbon_metric_to_json(metric)
        deserialized = deserialize_carbon_metric_from_json(json_str)

        assert deserialized.namespace == metric.namespace
        assert deserialized.emissions_gco2 == metric.emissions_gco2


class TestExportFormatValidity:
    """
    Property 14: Export Format Validity
    CSV and JSON exports produce valid formats.
    Validates: Requirements 2.5
    """

    @settings(max_examples=100)
    @given(metrics=st.lists(carbon_metric_strategy(), min_size=1, max_size=10))
    def test_csv_export_is_valid(self, metrics: list[CarbonMetric]):
        """Feature: kepler-greenops-sustainability, Property 14: CSV Export Validity"""
        csv_output = export_to_csv(metrics)

        # Verify CSV is parseable
        reader = csv.DictReader(io.StringIO(csv_output))
        rows = list(reader)

        assert len(rows) == len(metrics)
        assert "namespace" in reader.fieldnames
        assert "emissions_gco2" in reader.fieldnames

    @settings(max_examples=100)
    @given(metrics=st.lists(carbon_metric_strategy(), min_size=1, max_size=10))
    def test_json_export_is_valid(self, metrics: list[CarbonMetric]):
        """Feature: kepler-greenops-sustainability, Property 14: JSON Export Validity"""
        json_output = export_to_json(metrics)

        # Verify JSON is parseable
        parsed = json.loads(json_output)

        assert isinstance(parsed, list)
        assert len(parsed) == len(metrics)
        assert all("namespace" in item for item in parsed)
        assert all("emissions_gco2" in item for item in parsed)


class TestMalformedJsonRejection:
    """
    Property 15: Malformed JSON Rejection
    Malformed JSON raises ValidationError.
    Validates: Requirements 7.4
    """

    @pytest.mark.parametrize(
        "invalid_json",
        [
            "",
            "not json",
            "{",
            '{"incomplete": ',
            "null",
            "[]",
            "123",
            '"string"',
        ],
    )
    def test_malformed_json_raises_error(self, invalid_json: str):
        """Feature: kepler-greenops-sustainability, Property 15: Malformed JSON Rejection"""
        with pytest.raises(ValidationError):
            deserialize_carbon_metric_from_json(invalid_json)


class TestAlertRuleGeneration:
    """
    Property 9: Alert Rule Generation
    Generated rule contains correct threshold value.
    Validates: Requirements 5.1, 5.3
    """

    @settings(max_examples=100)
    @given(
        namespace=st.one_of(st.none(), namespace_strategy),
        deployment=st.one_of(st.none(), pod_strategy),
        energy_threshold=decimal_positive,
        carbon_threshold=decimal_positive,
        cost_threshold=decimal_positive,
        severity=st.sampled_from(["warning", "critical"]),
    )
    def test_alert_rule_contains_threshold(
        self,
        namespace,
        deployment,
        energy_threshold,
        carbon_threshold,
        cost_threshold,
        severity,
    ):
        """Feature: kepler-greenops-sustainability, Property 9: Alert Rule Generation"""
        threshold = AlertThreshold(
            namespace=namespace,
            deployment=deployment,
            energy_threshold_kwh=energy_threshold,
            carbon_threshold_gco2=carbon_threshold,
            cost_threshold=cost_threshold,
            severity=severity,
        )

        rule = generate_alert_rule(threshold)

        assert str(energy_threshold) in rule.expr
        assert rule.severity == severity
        assert rule.name.endswith(severity)

        if namespace:
            assert namespace in rule.expr
