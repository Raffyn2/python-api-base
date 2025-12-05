"""
Serializer module for sustainability metrics.

Provides JSON serialization/deserialization and export functions
for carbon metrics and sustainability data.
"""

import csv
import io
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.infrastructure.sustainability.models import (
    CarbonIntensity,
    CarbonMetric,
    SustainabilityReport,
)


class ValidationError(Exception):
    """Raised when JSON validation fails."""

    pass


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize_carbon_intensity(intensity: CarbonIntensity) -> dict[str, Any]:
    """Serialize CarbonIntensity to dictionary."""
    return {
        "region": intensity.region,
        "intensity_gco2_per_kwh": str(intensity.intensity_gco2_per_kwh),
        "timestamp": intensity.timestamp.isoformat(),
        "source": intensity.source,
        "is_default": intensity.is_default,
    }


def deserialize_carbon_intensity(data: dict[str, Any]) -> CarbonIntensity:
    """Deserialize dictionary to CarbonIntensity."""
    return CarbonIntensity(
        region=data["region"],
        intensity_gco2_per_kwh=Decimal(data["intensity_gco2_per_kwh"]),
        timestamp=datetime.fromisoformat(data["timestamp"]),
        source=data["source"],
        is_default=data.get("is_default", False),
    )


def serialize_carbon_metric(metric: CarbonMetric) -> dict[str, Any]:
    """
    Serialize CarbonMetric to dictionary.

    Property 1: Carbon Metrics Round-Trip Serialization
    Serializing and deserializing produces equivalent object.
    """
    return {
        "namespace": metric.namespace,
        "pod": metric.pod,
        "container": metric.container,
        "energy_kwh": str(metric.energy_kwh),
        "carbon_intensity": serialize_carbon_intensity(metric.carbon_intensity),
        "emissions_gco2": str(metric.emissions_gco2),
        "timestamp": metric.timestamp.isoformat(),
        "confidence_lower": str(metric.confidence_lower),
        "confidence_upper": str(metric.confidence_upper),
    }


def deserialize_carbon_metric(data: dict[str, Any]) -> CarbonMetric:
    """
    Deserialize dictionary to CarbonMetric.

    Property 1: Carbon Metrics Round-Trip Serialization
    Serializing and deserializing produces equivalent object.
    """
    required_fields = [
        "namespace",
        "pod",
        "container",
        "energy_kwh",
        "carbon_intensity",
        "emissions_gco2",
        "timestamp",
        "confidence_lower",
        "confidence_upper",
    ]
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    return CarbonMetric(
        namespace=data["namespace"],
        pod=data["pod"],
        container=data["container"],
        energy_kwh=Decimal(data["energy_kwh"]),
        carbon_intensity=deserialize_carbon_intensity(data["carbon_intensity"]),
        emissions_gco2=Decimal(data["emissions_gco2"]),
        timestamp=datetime.fromisoformat(data["timestamp"]),
        confidence_lower=Decimal(data["confidence_lower"]),
        confidence_upper=Decimal(data["confidence_upper"]),
    )


def serialize_carbon_metric_to_json(metric: CarbonMetric) -> str:
    """Serialize CarbonMetric to JSON string."""
    return json.dumps(serialize_carbon_metric(metric), cls=DecimalEncoder)


def deserialize_carbon_metric_from_json(json_str: str) -> CarbonMetric:
    """
    Deserialize JSON string to CarbonMetric.

    Property 15: Malformed JSON Rejection
    Malformed JSON raises ValidationError with descriptive message.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {e}")

    if not isinstance(data, dict):
        raise ValidationError("JSON must be an object")

    return deserialize_carbon_metric(data)


def serialize_report(report: SustainabilityReport) -> dict[str, Any]:
    """Serialize SustainabilityReport to dictionary."""
    return {
        "namespace": report.namespace,
        "period_start": report.period_start.isoformat(),
        "period_end": report.period_end.isoformat(),
        "total_energy_kwh": str(report.total_energy_kwh),
        "total_emissions_gco2": str(report.total_emissions_gco2),
        "total_cost": str(report.total_cost),
        "currency": report.currency,
        "baseline_emissions_gco2": (
            str(report.baseline_emissions_gco2)
            if report.baseline_emissions_gco2 is not None
            else None
        ),
        "target_emissions_gco2": (
            str(report.target_emissions_gco2)
            if report.target_emissions_gco2 is not None
            else None
        ),
        "progress_percentage": (
            str(report.progress_percentage)
            if report.progress_percentage is not None
            else None
        ),
    }


def export_to_csv(data: list[CarbonMetric]) -> str:
    """
    Export carbon metrics to CSV format.

    Property 14: Export Format Validity
    CSV export produces valid CSV with headers.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "namespace",
        "pod",
        "container",
        "energy_kwh",
        "emissions_gco2",
        "timestamp",
        "confidence_lower",
        "confidence_upper",
        "carbon_intensity_region",
        "carbon_intensity_gco2_per_kwh",
    ]
    writer.writerow(headers)

    for metric in data:
        writer.writerow([
            metric.namespace,
            metric.pod,
            metric.container,
            str(metric.energy_kwh),
            str(metric.emissions_gco2),
            metric.timestamp.isoformat(),
            str(metric.confidence_lower),
            str(metric.confidence_upper),
            metric.carbon_intensity.region,
            str(metric.carbon_intensity.intensity_gco2_per_kwh),
        ])

    return output.getvalue()


def export_to_json(data: list[CarbonMetric]) -> str:
    """
    Export carbon metrics to JSON format.

    Property 14: Export Format Validity
    JSON export produces valid JSON array.
    """
    return json.dumps(
        [serialize_carbon_metric(metric) for metric in data],
        cls=DecimalEncoder,
        indent=2,
    )


def parse_csv(csv_content: str) -> list[dict[str, str]]:
    """Parse CSV content to list of dictionaries."""
    reader = csv.DictReader(io.StringIO(csv_content))
    return list(reader)


def validate_json(json_str: str) -> bool:
    """Validate JSON string is well-formed."""
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False
