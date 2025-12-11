"""Sustainability module for Kepler + GreenOps integration.

Provides energy consumption metrics, carbon emission calculations,
and sustainability reporting capabilities.
"""

from infrastructure.sustainability.alerts import (
    generate_alert_rule,
    generate_all_alerts,
    generate_carbon_alert_rule,
    generate_cost_alert_rule,
)
from infrastructure.sustainability.calculator import (
    aggregate_emissions,
    calculate_cost,
    calculate_efficiency,
    calculate_emissions,
    calculate_progress,
    calculate_savings,
    calculate_trend,
    create_carbon_metrics,
)
from infrastructure.sustainability.config import (
    SustainabilitySettings,
    get_sustainability_settings,
)
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
from infrastructure.sustainability.service import SustainabilityService

__all__ = [
    "AlertRule",
    "AlertThreshold",
    "CarbonIntensity",
    "CarbonMetric",
    "CarbonUnit",
    "EnergyCost",
    "EnergyEfficiency",
    "EnergyMetric",
    "EnergyUnit",
    "SustainabilityReport",
    "SustainabilityService",
    "SustainabilitySettings",
    "aggregate_emissions",
    "calculate_cost",
    "calculate_efficiency",
    "calculate_emissions",
    "calculate_progress",
    "calculate_savings",
    "calculate_trend",
    "create_carbon_metrics",
    "generate_alert_rule",
    "generate_all_alerts",
    "generate_carbon_alert_rule",
    "generate_cost_alert_rule",
    "get_sustainability_settings",
]
