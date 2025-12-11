"""External API clients for sustainability services.

Provides clients for carbon intensity data and Prometheus metrics
with circuit breaker pattern for fault tolerance.
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import httpx
import structlog

from infrastructure.sustainability.config import SustainabilitySettings
from infrastructure.sustainability.models import CarbonIntensity, EnergyMetric

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED

    def record_success(self) -> None:
        """Record successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_execute(self) -> bool:
        """Check if call can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                # Ensure both datetimes are timezone-aware for comparison
                last_failure = self.last_failure_time
                if last_failure.tzinfo is None:
                    last_failure = last_failure.replace(tzinfo=UTC)
                elapsed = (datetime.now(UTC) - last_failure).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        return True  # HALF_OPEN allows one attempt


class CarbonIntensityClient:
    """Client for fetching carbon intensity data."""

    def __init__(self, settings: SustainabilitySettings) -> None:
        self.settings = settings
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )
        self._client = httpx.AsyncClient(timeout=settings.carbon_intensity_timeout_seconds)

    async def get_carbon_intensity(self, region: str) -> CarbonIntensity:
        """Fetch carbon intensity for a region.

        Falls back to default values if API unavailable.
        """
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker open, using default intensity")
            return self._get_default_intensity()

        try:
            intensity = await self._fetch_intensity(region)
            self.circuit_breaker.record_success()
            return intensity
        except Exception:
            logger.exception(
                "Failed to fetch carbon intensity",
                region=region,
                operation="CARBON_FETCH",
            )
            self.circuit_breaker.record_failure()
            return self._get_default_intensity()

    async def _fetch_intensity(self, region: str) -> CarbonIntensity:
        """Fetch intensity from external API."""
        headers = {}
        if self.settings.carbon_intensity_api_key:
            headers["auth-token"] = self.settings.carbon_intensity_api_key

        url = f"{self.settings.carbon_intensity_api_url}/carbon-intensity/latest"
        params = {"zone": region}

        response = await self._client.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        return CarbonIntensity(
            region=region,
            intensity_gco2_per_kwh=Decimal(str(data.get("carbonIntensity", 400))),
            timestamp=datetime.now(UTC),
            source="electricity-maps",
            is_default=False,
        )

    def _get_default_intensity(self) -> CarbonIntensity:
        """Get default carbon intensity."""
        return CarbonIntensity(
            region=self.settings.default_region,
            intensity_gco2_per_kwh=self.settings.default_carbon_intensity_gco2_per_kwh,
            timestamp=datetime.now(UTC),
            source="default",
            is_default=True,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class PrometheusClient:
    """Client for querying Prometheus metrics."""

    def __init__(self, settings: SustainabilitySettings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(timeout=settings.prometheus_timeout_seconds)

    async def query(self, promql: str) -> list[dict[str, Any]]:
        """Execute PromQL query."""
        url = f"{self.settings.prometheus_url}/api/v1/query"
        params = {"query": promql}

        response = await self._client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "success":
            raise RuntimeError(f"Prometheus query failed: {data.get('error')}")

        return data.get("data", {}).get("result", [])

    async def query_range(
        self,
        promql: str,
        start: datetime,
        end: datetime,
        step: str = "1m",
    ) -> list[dict[str, Any]]:
        """Execute PromQL range query."""
        url = f"{self.settings.prometheus_url}/api/v1/query_range"
        params = {
            "query": promql,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": step,
        }

        response = await self._client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "success":
            raise RuntimeError(f"Prometheus query failed: {data.get('error')}")

        return data.get("data", {}).get("result", [])

    async def get_kepler_energy_metrics(
        self,
        namespace: str | None = None,
    ) -> list[EnergyMetric]:
        """Fetch Kepler energy metrics from Prometheus."""
        query = "kepler_container_joules_total"
        if namespace:
            query = f'kepler_container_joules_total{{namespace="{namespace}"}}'

        results = await self.query(query)
        metrics = []

        for result in results:
            metric_labels = result.get("metric", {})
            value = result.get("value", [None, "0"])

            metrics.append(
                EnergyMetric(
                    namespace=metric_labels.get("namespace", "unknown"),
                    pod=metric_labels.get("pod", "unknown"),
                    container=metric_labels.get("container", "unknown"),
                    energy_joules=Decimal(str(value[1])),
                    timestamp=datetime.now(UTC),
                    source=metric_labels.get("source", "kepler"),
                )
            )

        return metrics

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
