"""
Data models for sustainability metrics.

Provides frozen dataclasses for energy consumption, carbon emissions,
cost calculations, and alert configurations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class EnergyUnit(Enum):
    """Energy measurement units."""

    JOULES = "J"
    KILOWATT_HOURS = "kWh"
    WATT_HOURS = "Wh"


class CarbonUnit(Enum):
    """Carbon emission units."""

    GRAMS_CO2 = "gCO2"
    KILOGRAMS_CO2 = "kgCO2"
    TONS_CO2 = "tCO2"


JOULES_PER_KWH = Decimal("3600000")
GRAMS_PER_KG = Decimal("1000")
KG_PER_TON = Decimal("1000")


@dataclass(frozen=True)
class EnergyMetric:
    """Energy consumption metric for a container/pod."""

    namespace: str
    pod: str
    container: str
    energy_joules: Decimal
    timestamp: datetime
    source: str  # "rapl", "acpi", "model"

    def __post_init__(self) -> None:
        if self.energy_joules < 0:
            raise ValueError("energy_joules must be non-negative")

    @property
    def energy_kwh(self) -> Decimal:
        """Convert energy from joules to kilowatt-hours."""
        return self.energy_joules / JOULES_PER_KWH

    @property
    def energy_wh(self) -> Decimal:
        """Convert energy from joules to watt-hours."""
        return self.energy_joules / Decimal("3600")


@dataclass(frozen=True)
class CarbonIntensity:
    """Regional carbon intensity factor (gCO2 per kWh)."""

    region: str
    intensity_gco2_per_kwh: Decimal
    timestamp: datetime
    source: str
    is_default: bool = False

    def __post_init__(self) -> None:
        if self.intensity_gco2_per_kwh < 0:
            raise ValueError("intensity_gco2_per_kwh must be non-negative")


@dataclass(frozen=True)
class CarbonMetric:
    """Carbon emission metric calculated from energy consumption."""

    namespace: str
    pod: str
    container: str
    energy_kwh: Decimal
    carbon_intensity: CarbonIntensity
    emissions_gco2: Decimal
    timestamp: datetime
    confidence_lower: Decimal
    confidence_upper: Decimal

    def __post_init__(self) -> None:
        if self.emissions_gco2 < 0:
            raise ValueError("emissions_gco2 must be non-negative")
        if self.confidence_lower > self.emissions_gco2:
            raise ValueError("confidence_lower cannot exceed emissions_gco2")
        if self.confidence_upper < self.emissions_gco2:
            raise ValueError("confidence_upper cannot be less than emissions_gco2")

    @classmethod
    def calculate(
        cls,
        energy: EnergyMetric,
        intensity: CarbonIntensity,
        confidence_margin: Decimal = Decimal("0.1"),
    ) -> "CarbonMetric":
        """Calculate carbon emissions from energy and intensity."""
        emissions = energy.energy_kwh * intensity.intensity_gco2_per_kwh
        return cls(
            namespace=energy.namespace,
            pod=energy.pod,
            container=energy.container,
            energy_kwh=energy.energy_kwh,
            carbon_intensity=intensity,
            emissions_gco2=emissions,
            timestamp=energy.timestamp,
            confidence_lower=emissions * (1 - confidence_margin),
            confidence_upper=emissions * (1 + confidence_margin),
        )

    @property
    def emissions_kgco2(self) -> Decimal:
        """Convert emissions to kilograms CO2."""
        return self.emissions_gco2 / GRAMS_PER_KG

    @property
    def emissions_tco2(self) -> Decimal:
        """Convert emissions to tons CO2."""
        return self.emissions_kgco2 / KG_PER_TON


@dataclass(frozen=True)
class EnergyCost:
    """Energy cost calculation for a period."""

    energy_kwh: Decimal
    price_per_kwh: Decimal
    total_cost: Decimal
    currency: str
    period_start: datetime
    period_end: datetime

    def __post_init__(self) -> None:
        if self.energy_kwh < 0:
            raise ValueError("energy_kwh must be non-negative")
        if self.price_per_kwh < 0:
            raise ValueError("price_per_kwh must be non-negative")

    @classmethod
    def calculate(
        cls,
        energy_kwh: Decimal,
        price_per_kwh: Decimal,
        currency: str,
        period_start: datetime,
        period_end: datetime,
    ) -> "EnergyCost":
        """Calculate energy cost from consumption and price."""
        return cls(
            energy_kwh=energy_kwh,
            price_per_kwh=price_per_kwh,
            total_cost=energy_kwh * price_per_kwh,
            currency=currency,
            period_start=period_start,
            period_end=period_end,
        )


@dataclass(frozen=True)
class SustainabilityReport:
    """Aggregated sustainability report for a namespace."""

    namespace: str
    period_start: datetime
    period_end: datetime
    total_energy_kwh: Decimal
    total_emissions_gco2: Decimal
    total_cost: Decimal
    currency: str
    baseline_emissions_gco2: Decimal | None = None
    target_emissions_gco2: Decimal | None = None

    @property
    def progress_percentage(self) -> Decimal | None:
        """Calculate progress towards emission reduction target."""
        if self.baseline_emissions_gco2 and self.target_emissions_gco2:
            reduction = self.baseline_emissions_gco2 - self.total_emissions_gco2
            target_reduction = self.baseline_emissions_gco2 - self.target_emissions_gco2
            if target_reduction > 0:
                return (reduction / target_reduction) * Decimal("100")
        return None

    @property
    def reduction_percentage(self) -> Decimal | None:
        """Calculate percentage reduction from baseline."""
        if self.baseline_emissions_gco2 and self.baseline_emissions_gco2 > 0:
            reduction = self.baseline_emissions_gco2 - self.total_emissions_gco2
            return (reduction / self.baseline_emissions_gco2) * Decimal("100")
        return None


@dataclass(frozen=True)
class EnergyEfficiency:
    """Energy efficiency metrics for a deployment."""

    namespace: str
    deployment: str
    total_energy_joules: Decimal
    requests_count: int
    transactions_count: int
    period_start: datetime
    period_end: datetime

    def __post_init__(self) -> None:
        if self.requests_count < 0:
            raise ValueError("requests_count must be non-negative")
        if self.transactions_count < 0:
            raise ValueError("transactions_count must be non-negative")

    @property
    def energy_per_request_joules(self) -> Decimal | None:
        """Calculate energy per request in joules."""
        if self.requests_count > 0:
            return self.total_energy_joules / Decimal(self.requests_count)
        return None

    @property
    def energy_per_transaction_joules(self) -> Decimal | None:
        """Calculate energy per transaction in joules."""
        if self.transactions_count > 0:
            return self.total_energy_joules / Decimal(self.transactions_count)
        return None


@dataclass(frozen=True)
class AlertThreshold:
    """Alert threshold configuration for sustainability metrics."""

    namespace: str | None  # None = cluster-wide
    deployment: str | None  # None = namespace-wide
    energy_threshold_kwh: Decimal
    carbon_threshold_gco2: Decimal
    cost_threshold: Decimal
    severity: str = "warning"  # "warning" or "critical"

    def __post_init__(self) -> None:
        if self.severity not in ("warning", "critical"):
            raise ValueError("severity must be 'warning' or 'critical'")


@dataclass(frozen=True)
class AlertRule:
    """Prometheus alert rule definition."""

    name: str
    expr: str
    duration: str
    severity: str
    annotations: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)

    def to_prometheus_format(self) -> dict:
        """Convert to Prometheus alert rule format."""
        return {
            "alert": self.name,
            "expr": self.expr,
            "for": self.duration,
            "labels": {"severity": self.severity, **self.labels},
            "annotations": self.annotations,
        }
