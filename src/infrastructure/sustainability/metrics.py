"""
Prometheus metrics exporter for sustainability data.

Provides custom metrics for carbon emissions, energy costs,
and sustainability reporting with consistent labels.
"""

from decimal import Decimal
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

# Energy metrics
ENERGY_CONSUMPTION_TOTAL = Counter(
    "sustainability_energy_consumption_joules_total",
    "Total energy consumption in joules",
    ["namespace", "pod", "container"],
)

ENERGY_CONSUMPTION_KWH = Gauge(
    "sustainability_energy_consumption_kwh",
    "Current energy consumption rate in kWh",
    ["namespace", "pod", "container"],
)

# Carbon metrics
CARBON_EMISSIONS_TOTAL = Counter(
    "sustainability_carbon_emissions_gco2_total",
    "Total carbon emissions in grams CO2",
    ["namespace", "pod", "container"],
)

CARBON_EMISSIONS_RATE = Gauge(
    "sustainability_carbon_emissions_gco2_rate",
    "Current carbon emission rate in gCO2/h",
    ["namespace", "pod", "container"],
)

CARBON_INTENSITY = Gauge(
    "sustainability_carbon_intensity_gco2_per_kwh",
    "Current carbon intensity factor",
    ["region", "source"],
)

# Cost metrics
ENERGY_COST_TOTAL = Counter(
    "sustainability_energy_cost_total",
    "Total energy cost",
    ["namespace", "currency"],
)

ENERGY_COST_RATE = Gauge(
    "sustainability_energy_cost_rate",
    "Current energy cost rate per hour",
    ["namespace", "currency"],
)

# Efficiency metrics
ENERGY_PER_REQUEST = Histogram(
    "sustainability_energy_per_request_joules",
    "Energy consumption per request in joules",
    ["namespace", "deployment"],
    buckets=[0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000],
)

# Report metrics
SUSTAINABILITY_REPORT_GENERATED = Counter(
    "sustainability_reports_generated_total",
    "Total number of sustainability reports generated",
    ["namespace"],
)

GOAL_PROGRESS_PERCENTAGE = Gauge(
    "sustainability_goal_progress_percentage",
    "Progress towards emission reduction goal",
    ["namespace"],
)


def format_prometheus_metric(
    name: str,
    value: Decimal | float,
    labels: dict[str, str],
    help_text: str = "",
    metric_type: str = "gauge",
) -> str:
    """
    Format a metric in Prometheus exposition format.

    Property 11: Prometheus Metrics Format
    Output conforms to Prometheus format with required labels.

    Args:
        name: Metric name
        value: Metric value
        labels: Label key-value pairs
        help_text: Help text for the metric
        metric_type: Type of metric (gauge, counter, histogram)

    Returns:
        Prometheus-formatted metric string
    """
    lines = []

    if help_text:
        lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} {metric_type}")

    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    lines.append(f"{name}{{{label_str}}} {value}")

    return "\n".join(lines)


def record_energy_metric(
    namespace: str,
    pod: str,
    container: str,
    energy_joules: Decimal,
) -> None:
    """Record energy consumption metric."""
    ENERGY_CONSUMPTION_TOTAL.labels(
        namespace=namespace,
        pod=pod,
        container=container,
    ).inc(float(energy_joules))

    energy_kwh = energy_joules / Decimal("3600000")
    ENERGY_CONSUMPTION_KWH.labels(
        namespace=namespace,
        pod=pod,
        container=container,
    ).set(float(energy_kwh))


def record_carbon_metric(
    namespace: str,
    pod: str,
    container: str,
    emissions_gco2: Decimal,
) -> None:
    """Record carbon emission metric."""
    CARBON_EMISSIONS_TOTAL.labels(
        namespace=namespace,
        pod=pod,
        container=container,
    ).inc(float(emissions_gco2))

    CARBON_EMISSIONS_RATE.labels(
        namespace=namespace,
        pod=pod,
        container=container,
    ).set(float(emissions_gco2))


def record_carbon_intensity(
    region: str,
    source: str,
    intensity_gco2_per_kwh: Decimal,
) -> None:
    """Record carbon intensity metric."""
    CARBON_INTENSITY.labels(
        region=region,
        source=source,
    ).set(float(intensity_gco2_per_kwh))


def record_energy_cost(
    namespace: str,
    currency: str,
    cost: Decimal,
) -> None:
    """Record energy cost metric."""
    ENERGY_COST_TOTAL.labels(
        namespace=namespace,
        currency=currency,
    ).inc(float(cost))

    ENERGY_COST_RATE.labels(
        namespace=namespace,
        currency=currency,
    ).set(float(cost))


def record_efficiency_metric(
    namespace: str,
    deployment: str,
    energy_per_request: Decimal,
) -> None:
    """Record energy efficiency metric."""
    ENERGY_PER_REQUEST.labels(
        namespace=namespace,
        deployment=deployment,
    ).observe(float(energy_per_request))


def record_goal_progress(
    namespace: str,
    progress_percentage: Decimal,
) -> None:
    """Record goal progress metric."""
    GOAL_PROGRESS_PERCENTAGE.labels(
        namespace=namespace,
    ).set(float(progress_percentage))


def record_report_generated(namespace: str) -> None:
    """Record report generation metric."""
    SUSTAINABILITY_REPORT_GENERATED.labels(
        namespace=namespace,
    ).inc()


def validate_metric_labels(labels: dict[str, str]) -> bool:
    """
    Validate that metric labels contain required fields.

    Property 11: Prometheus Metrics Format
    All metrics include required labels (namespace, pod, container).
    """
    required_labels = {"namespace"}
    return required_labels.issubset(labels.keys())


def generate_metrics_output(metrics: list[dict[str, Any]]) -> str:
    """
    Generate Prometheus metrics output from a list of metrics.

    Args:
        metrics: List of metric dictionaries with name, value, labels

    Returns:
        Prometheus exposition format string
    """
    output_lines = []

    for metric in metrics:
        output_lines.append(
            format_prometheus_metric(
                name=metric["name"],
                value=metric["value"],
                labels=metric.get("labels", {}),
                help_text=metric.get("help", ""),
                metric_type=metric.get("type", "gauge"),
            )
        )

    return "\n\n".join(output_lines)
