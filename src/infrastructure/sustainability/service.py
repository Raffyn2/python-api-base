"""
Sustainability service for orchestrating metrics collection and reporting.

Provides high-level interface for energy metrics, carbon calculations,
and sustainability reporting.
"""

import logging
from datetime import datetime
from decimal import Decimal

from src.infrastructure.sustainability.calculator import (
    aggregate_emissions,
    calculate_cost,
    calculate_progress,
    calculate_savings,
    calculate_trend,
    create_carbon_metrics,
)
from src.infrastructure.sustainability.client import (
    CarbonIntensityClient,
    PrometheusClient,
)
from src.infrastructure.sustainability.config import (
    SustainabilitySettings,
    get_sustainability_settings,
)
from src.infrastructure.sustainability.models import (
    CarbonMetric,
    EnergyCost,
    EnergyMetric,
    SustainabilityReport,
)
from src.infrastructure.sustainability.serializer import (
    export_to_csv,
    export_to_json,
    serialize_carbon_metric,
    serialize_report,
)

logger = logging.getLogger(__name__)


class SustainabilityService:
    """Service for sustainability metrics and reporting."""

    def __init__(
        self,
        settings: SustainabilitySettings | None = None,
        carbon_client: CarbonIntensityClient | None = None,
        prometheus_client: PrometheusClient | None = None,
    ):
        self.settings = settings or get_sustainability_settings()
        self._carbon_client = carbon_client
        self._prometheus_client = prometheus_client

    @property
    def carbon_client(self) -> CarbonIntensityClient:
        """Get or create carbon intensity client."""
        if self._carbon_client is None:
            self._carbon_client = CarbonIntensityClient(self.settings)
        return self._carbon_client

    @property
    def prometheus_client(self) -> PrometheusClient:
        """Get or create Prometheus client."""
        if self._prometheus_client is None:
            self._prometheus_client = PrometheusClient(self.settings)
        return self._prometheus_client

    async def get_energy_metrics(
        self,
        namespace: str | None = None,
    ) -> list[EnergyMetric]:
        """Fetch energy metrics from Kepler via Prometheus."""
        return await self.prometheus_client.get_kepler_energy_metrics(namespace)

    async def get_carbon_metrics(
        self,
        namespace: str | None = None,
        region: str | None = None,
    ) -> list[CarbonMetric]:
        """Calculate carbon metrics from energy consumption."""
        energy_metrics = await self.get_energy_metrics(namespace)
        intensity = await self.carbon_client.get_carbon_intensity(
            region or self.settings.default_region
        )
        return create_carbon_metrics(energy_metrics, intensity)

    async def get_emissions_by_namespace(
        self,
        namespace: str | None = None,
    ) -> dict[str, Decimal]:
        """Get aggregated emissions by namespace."""
        metrics = await self.get_carbon_metrics(namespace)
        return aggregate_emissions(metrics, "namespace")

    async def calculate_energy_cost(
        self,
        namespace: str | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> EnergyCost:
        """Calculate energy cost for a namespace."""
        energy_metrics = await self.get_energy_metrics(namespace)
        total_energy_kwh = sum(m.energy_kwh for m in energy_metrics)

        now = datetime.now()
        return EnergyCost.calculate(
            energy_kwh=total_energy_kwh,
            price_per_kwh=self.settings.electricity_price_per_kwh,
            currency=self.settings.currency,
            period_start=period_start or now,
            period_end=period_end or now,
        )

    async def generate_report(
        self,
        namespace: str,
        period_start: datetime,
        period_end: datetime,
        baseline_emissions: Decimal | None = None,
        target_emissions: Decimal | None = None,
    ) -> SustainabilityReport:
        """Generate sustainability report for a namespace."""
        carbon_metrics = await self.get_carbon_metrics(namespace)
        energy_cost = await self.calculate_energy_cost(
            namespace, period_start, period_end
        )

        total_energy_kwh = sum(m.energy_kwh for m in carbon_metrics)
        total_emissions = sum(m.emissions_gco2 for m in carbon_metrics)

        return SustainabilityReport(
            namespace=namespace,
            period_start=period_start,
            period_end=period_end,
            total_energy_kwh=total_energy_kwh,
            total_emissions_gco2=total_emissions,
            total_cost=energy_cost.total_cost,
            currency=energy_cost.currency,
            baseline_emissions_gco2=baseline_emissions,
            target_emissions_gco2=target_emissions,
        )

    async def get_progress(
        self,
        namespace: str,
        baseline: Decimal,
        target: Decimal,
    ) -> Decimal | None:
        """Calculate progress towards emission reduction target."""
        metrics = await self.get_carbon_metrics(namespace)
        current = sum(m.emissions_gco2 for m in metrics)
        return calculate_progress(baseline, current, target)

    async def get_cost_savings(
        self,
        namespace: str,
        baseline_cost: Decimal,
    ) -> Decimal:
        """Calculate cost savings compared to baseline."""
        cost = await self.calculate_energy_cost(namespace)
        return calculate_savings(baseline_cost, cost.total_cost)

    async def get_trend(
        self,
        namespace: str,
        previous_emissions: Decimal,
    ) -> Decimal | None:
        """Calculate emission trend compared to previous period."""
        metrics = await self.get_carbon_metrics(namespace)
        current = sum(m.emissions_gco2 for m in metrics)
        return calculate_trend(previous_emissions, current)

    def export_metrics_csv(self, metrics: list[CarbonMetric]) -> str:
        """Export carbon metrics to CSV format."""
        return export_to_csv(metrics)

    def export_metrics_json(self, metrics: list[CarbonMetric]) -> str:
        """Export carbon metrics to JSON format."""
        return export_to_json(metrics)

    def serialize_metric(self, metric: CarbonMetric) -> dict:
        """Serialize a single carbon metric."""
        return serialize_carbon_metric(metric)

    def serialize_report_data(self, report: SustainabilityReport) -> dict:
        """Serialize sustainability report."""
        return serialize_report(report)

    async def close(self) -> None:
        """Close all clients."""
        if self._carbon_client:
            await self._carbon_client.close()
        if self._prometheus_client:
            await self._prometheus_client.close()
