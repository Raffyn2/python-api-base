"""
Alert generator module for sustainability metrics.

Generates Prometheus alert rules for energy consumption
and carbon emission thresholds.
"""

from decimal import Decimal

from src.infrastructure.sustainability.models import AlertRule, AlertThreshold


def generate_alert_rule(threshold: AlertThreshold) -> AlertRule:
    """
    Generate Prometheus alert rule from threshold configuration.

    Property 9: Alert Rule Generation
    Generated rule contains correct threshold value in expression.

    Args:
        threshold: Alert threshold configuration

    Returns:
        AlertRule with valid Prometheus expression
    """
    # Build label selector
    labels = []
    if threshold.namespace:
        labels.append(f'namespace="{threshold.namespace}"')
    if threshold.deployment:
        labels.append(f'deployment="{threshold.deployment}"')

    label_selector = "{" + ",".join(labels) + "}" if labels else ""

    # Build alert name
    scope = "cluster"
    if threshold.namespace:
        scope = f"namespace_{threshold.namespace}"
    if threshold.deployment:
        scope = f"deployment_{threshold.deployment}"

    name = f"sustainability_energy_threshold_{scope}_{threshold.severity}"

    # Build PromQL expression
    expr = (
        f"sum(rate(kepler_container_joules_total{label_selector}[5m])) "
        f"/ 3600000 > {threshold.energy_threshold_kwh}"
    )

    return AlertRule(
        name=name,
        expr=expr,
        duration="5m",
        severity=threshold.severity,
        annotations={
            "summary": f"Energy consumption exceeds threshold ({threshold.energy_threshold_kwh} kWh)",
            "description": (
                f"Energy consumption in {scope} has exceeded "
                f"{threshold.energy_threshold_kwh} kWh for more than 5 minutes."
            ),
            "runbook_url": "https://docs.example.com/runbooks/sustainability/energy-threshold",
        },
        labels={
            "team": "platform",
            "component": "sustainability",
        },
    )


def generate_carbon_alert_rule(threshold: AlertThreshold) -> AlertRule:
    """Generate alert rule for carbon emissions threshold."""
    labels = []
    if threshold.namespace:
        labels.append(f'namespace="{threshold.namespace}"')
    if threshold.deployment:
        labels.append(f'deployment="{threshold.deployment}"')

    label_selector = "{" + ",".join(labels) + "}" if labels else ""

    scope = "cluster"
    if threshold.namespace:
        scope = f"namespace_{threshold.namespace}"
    if threshold.deployment:
        scope = f"deployment_{threshold.deployment}"

    name = f"sustainability_carbon_threshold_{scope}_{threshold.severity}"

    # Carbon = Energy (kWh) * Intensity (gCO2/kWh)
    # Using default intensity of 400 gCO2/kWh
    expr = (
        f"(sum(rate(kepler_container_joules_total{label_selector}[5m])) "
        f"/ 3600000) * 400 > {threshold.carbon_threshold_gco2}"
    )

    return AlertRule(
        name=name,
        expr=expr,
        duration="5m",
        severity=threshold.severity,
        annotations={
            "summary": f"Carbon emissions exceed threshold ({threshold.carbon_threshold_gco2} gCO2)",
            "description": (
                f"Carbon emissions in {scope} have exceeded "
                f"{threshold.carbon_threshold_gco2} gCO2 for more than 5 minutes."
            ),
            "runbook_url": "https://docs.example.com/runbooks/sustainability/carbon-threshold",
        },
        labels={
            "team": "platform",
            "component": "sustainability",
        },
    )


def generate_cost_alert_rule(threshold: AlertThreshold, price_per_kwh: Decimal) -> AlertRule:
    """Generate alert rule for energy cost threshold."""
    labels = []
    if threshold.namespace:
        labels.append(f'namespace="{threshold.namespace}"')
    if threshold.deployment:
        labels.append(f'deployment="{threshold.deployment}"')

    label_selector = "{" + ",".join(labels) + "}" if labels else ""

    scope = "cluster"
    if threshold.namespace:
        scope = f"namespace_{threshold.namespace}"
    if threshold.deployment:
        scope = f"deployment_{threshold.deployment}"

    name = f"sustainability_cost_threshold_{scope}_{threshold.severity}"

    # Cost = Energy (kWh) * Price ($/kWh)
    expr = (
        f"(sum(rate(kepler_container_joules_total{label_selector}[5m])) "
        f"/ 3600000) * {price_per_kwh} > {threshold.cost_threshold}"
    )

    return AlertRule(
        name=name,
        expr=expr,
        duration="5m",
        severity=threshold.severity,
        annotations={
            "summary": f"Energy cost exceeds threshold (${threshold.cost_threshold})",
            "description": (
                f"Energy cost in {scope} has exceeded "
                f"${threshold.cost_threshold} for more than 5 minutes."
            ),
            "runbook_url": "https://docs.example.com/runbooks/sustainability/cost-threshold",
        },
        labels={
            "team": "platform",
            "component": "sustainability",
        },
    )


def generate_all_alerts(
    threshold: AlertThreshold,
    price_per_kwh: Decimal = Decimal("0.12"),
) -> list[AlertRule]:
    """Generate all alert rules for a threshold configuration."""
    return [
        generate_alert_rule(threshold),
        generate_carbon_alert_rule(threshold),
        generate_cost_alert_rule(threshold, price_per_kwh),
    ]
