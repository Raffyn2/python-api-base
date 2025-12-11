"""Calculator module for sustainability metrics.

Provides functions for carbon emission calculations, cost calculations,
aggregation, efficiency metrics, and goal tracking.
"""

from collections.abc import Sequence
from decimal import Decimal
from typing import Literal

from infrastructure.sustainability.models import (
    CarbonIntensity,
    CarbonMetric,
    EnergyMetric,
)


def calculate_emissions(energy_kwh: Decimal, intensity_gco2_per_kwh: Decimal) -> Decimal:
    """Calculate carbon emissions from energy consumption.

    Property 2: Carbon Emission Calculation
    For any energy (kWh) and intensity (gCO2/kWh), emissions = energy * intensity.

    Args:
        energy_kwh: Energy consumption in kilowatt-hours
        intensity_gco2_per_kwh: Carbon intensity in gCO2 per kWh

    Returns:
        Carbon emissions in grams CO2
    """
    if energy_kwh < 0:
        raise ValueError("energy_kwh must be non-negative")
    if intensity_gco2_per_kwh < 0:
        raise ValueError("intensity_gco2_per_kwh must be non-negative")
    return energy_kwh * intensity_gco2_per_kwh


def calculate_cost(energy_kwh: Decimal, price_per_kwh: Decimal) -> Decimal:
    """Calculate energy cost from consumption.

    Property 3: Energy Cost Calculation
    For any energy (kWh) and price ($/kWh), cost = energy * price.

    Args:
        energy_kwh: Energy consumption in kilowatt-hours
        price_per_kwh: Electricity price per kWh

    Returns:
        Total cost in the currency unit
    """
    if energy_kwh < 0:
        raise ValueError("energy_kwh must be non-negative")
    if price_per_kwh < 0:
        raise ValueError("price_per_kwh must be non-negative")
    return energy_kwh * price_per_kwh


def aggregate_emissions(
    metrics: Sequence[CarbonMetric],
    group_by: Literal["namespace", "pod", "container"] = "namespace",
) -> dict[str, Decimal]:
    """Aggregate carbon emissions by grouping key.

    Property 4: Emissions Aggregation Consistency
    Sum of individual emissions equals aggregated total.

    Args:
        metrics: Sequence of carbon metrics to aggregate
        group_by: Grouping key (namespace, pod, or container)

    Returns:
        Dictionary mapping group key to total emissions
    """
    aggregated: dict[str, Decimal] = {}
    for metric in metrics:
        key = getattr(metric, group_by)
        if key not in aggregated:
            aggregated[key] = Decimal(0)
        aggregated[key] += metric.emissions_gco2
    return aggregated


def calculate_efficiency(
    total_energy_joules: Decimal,
    requests_count: int,
    transactions_count: int,
) -> tuple[Decimal | None, Decimal | None]:
    """Calculate energy efficiency metrics.

    Property 6: Energy Efficiency Calculation
    For any energy and count > 0, efficiency = energy / count.

    Args:
        total_energy_joules: Total energy consumption in joules
        requests_count: Number of requests processed
        transactions_count: Number of transactions processed

    Returns:
        Tuple of (energy_per_request, energy_per_transaction) in joules
    """
    if total_energy_joules < 0:
        raise ValueError("total_energy_joules must be non-negative")
    if requests_count < 0:
        raise ValueError("requests_count must be non-negative")
    if transactions_count < 0:
        raise ValueError("transactions_count must be non-negative")

    energy_per_request = None
    energy_per_transaction = None

    if requests_count > 0:
        energy_per_request = total_energy_joules / Decimal(requests_count)
    if transactions_count > 0:
        energy_per_transaction = total_energy_joules / Decimal(transactions_count)

    return energy_per_request, energy_per_transaction


def calculate_progress(
    baseline: Decimal,
    current: Decimal,
    target: Decimal,
) -> Decimal | None:
    """Calculate progress towards emission reduction target.

    Property 5: Goal Progress Calculation
    progress = ((baseline - current) / (baseline - target)) * 100

    Args:
        baseline: Baseline emissions value
        current: Current emissions value
        target: Target emissions value

    Returns:
        Progress percentage (can exceed 100 if target exceeded)
    """
    if baseline < 0 or current < 0 or target < 0:
        raise ValueError("All values must be non-negative")

    target_reduction = baseline - target
    if target_reduction == 0:
        return None

    actual_reduction = baseline - current
    return (actual_reduction / target_reduction) * Decimal(100)


def calculate_savings(baseline_cost: Decimal, current_cost: Decimal) -> Decimal:
    """Calculate cost savings from energy optimization.

    Property 7: Cost Savings Calculation
    savings = baseline_cost - current_cost

    Args:
        baseline_cost: Baseline cost value
        current_cost: Current cost value

    Returns:
        Cost savings (negative if costs increased)
    """
    if baseline_cost < 0:
        raise ValueError("baseline_cost must be non-negative")
    if current_cost < 0:
        raise ValueError("current_cost must be non-negative")
    return baseline_cost - current_cost


def calculate_trend(previous: Decimal, current: Decimal) -> Decimal | None:
    """Calculate trend percentage between two periods.

    Property 8: Trend Calculation
    trend = ((current - previous) / previous) * 100

    Args:
        previous: Previous period value
        current: Current period value

    Returns:
        Trend percentage (positive = increase, negative = decrease)
    """
    if previous < 0 or current < 0:
        raise ValueError("Values must be non-negative")
    if previous == 0:
        return None
    return ((current - previous) / previous) * Decimal(100)


def create_carbon_metrics(
    energy_metrics: Sequence[EnergyMetric],
    intensity: CarbonIntensity,
    confidence_margin: Decimal = Decimal("0.1"),
) -> list[CarbonMetric]:
    """Create carbon metrics from energy metrics.

    Args:
        energy_metrics: Sequence of energy metrics
        intensity: Carbon intensity factor to use
        confidence_margin: Margin for confidence interval (default 10%)

    Returns:
        List of carbon metrics
    """
    return [CarbonMetric.calculate(energy, intensity, confidence_margin) for energy in energy_metrics]
