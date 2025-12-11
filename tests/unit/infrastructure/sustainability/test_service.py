"""Unit tests for sustainability service module."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.infrastructure.sustainability.config import SustainabilitySettings
from src.infrastructure.sustainability.models import (
    CarbonIntensity,
    CarbonMetric,
    EnergyMetric,
)
from src.infrastructure.sustainability.service import SustainabilityService


@pytest.fixture()
def settings() -> SustainabilitySettings:
    """Create test settings."""
    return SustainabilitySettings(
        electricity_price_per_kwh=Decimal("0.12"),
        currency="USD",
        default_carbon_intensity_gco2_per_kwh=Decimal(400),
    )


@pytest.fixture()
def mock_carbon_client() -> AsyncMock:
    """Create mock carbon intensity client."""
    client = AsyncMock()
    client.get_carbon_intensity.return_value = CarbonIntensity(
        region="us-east-1",
        intensity_gco2_per_kwh=Decimal(400),
        timestamp=datetime.now(),
        source="test",
        is_default=False,
    )
    return client


@pytest.fixture()
def mock_prometheus_client() -> AsyncMock:
    """Create mock Prometheus client."""
    client = AsyncMock()
    client.get_kepler_energy_metrics.return_value = [
        EnergyMetric(
            namespace="default",
            pod="api-pod",
            container="main",
            energy_joules=Decimal(3600000),  # 1 kWh
            timestamp=datetime.now(),
            source="rapl",
        )
    ]
    return client


class TestSustainabilityServiceInit:
    """Tests for SustainabilityService initialization."""

    def test_init_with_defaults(self) -> None:
        """Test service initializes with default settings."""
        service = SustainabilityService()

        assert service.settings is not None
        assert service._carbon_client is None
        assert service._prometheus_client is None

    def test_init_with_custom_settings(self, settings: SustainabilitySettings) -> None:
        """Test service initializes with custom settings."""
        service = SustainabilityService(settings=settings)

        assert service.settings == settings

    def test_init_with_clients(
        self,
        settings: SustainabilitySettings,
        mock_carbon_client: AsyncMock,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test service initializes with injected clients."""
        service = SustainabilityService(
            settings=settings,
            carbon_client=mock_carbon_client,
            prometheus_client=mock_prometheus_client,
        )

        assert service._carbon_client == mock_carbon_client
        assert service._prometheus_client == mock_prometheus_client


class TestSustainabilityServiceProperties:
    """Tests for SustainabilityService properties."""

    def test_carbon_client_lazy_init(self, settings: SustainabilitySettings) -> None:
        """Test carbon client is lazily initialized."""
        service = SustainabilityService(settings=settings)

        assert service._carbon_client is None
        client = service.carbon_client
        assert client is not None
        assert service._carbon_client is client

    def test_prometheus_client_lazy_init(self, settings: SustainabilitySettings) -> None:
        """Test Prometheus client is lazily initialized."""
        service = SustainabilityService(settings=settings)

        assert service._prometheus_client is None
        client = service.prometheus_client
        assert client is not None
        assert service._prometheus_client is client


class TestSustainabilityServiceMetrics:
    """Tests for SustainabilityService metric methods."""

    @pytest.mark.asyncio
    async def test_get_energy_metrics(
        self,
        settings: SustainabilitySettings,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test getting energy metrics."""
        service = SustainabilityService(
            settings=settings,
            prometheus_client=mock_prometheus_client,
        )

        metrics = await service.get_energy_metrics()

        assert len(metrics) == 1
        mock_prometheus_client.get_kepler_energy_metrics.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_get_energy_metrics_with_namespace(
        self,
        settings: SustainabilitySettings,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test getting energy metrics filtered by namespace."""
        service = SustainabilityService(
            settings=settings,
            prometheus_client=mock_prometheus_client,
        )

        await service.get_energy_metrics(namespace="production")

        mock_prometheus_client.get_kepler_energy_metrics.assert_called_once_with("production")

    @pytest.mark.asyncio
    async def test_get_carbon_metrics(
        self,
        settings: SustainabilitySettings,
        mock_carbon_client: AsyncMock,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test getting carbon metrics."""
        service = SustainabilityService(
            settings=settings,
            carbon_client=mock_carbon_client,
            prometheus_client=mock_prometheus_client,
        )

        metrics = await service.get_carbon_metrics()

        assert len(metrics) == 1
        assert metrics[0].emissions_gco2 == Decimal(400)  # 1 kWh * 400 gCO2/kWh

    @pytest.mark.asyncio
    async def test_get_emissions_by_namespace(
        self,
        settings: SustainabilitySettings,
        mock_carbon_client: AsyncMock,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test getting emissions aggregated by namespace."""
        service = SustainabilityService(
            settings=settings,
            carbon_client=mock_carbon_client,
            prometheus_client=mock_prometheus_client,
        )

        emissions = await service.get_emissions_by_namespace()

        assert "default" in emissions


class TestSustainabilityServiceCost:
    """Tests for SustainabilityService cost methods."""

    @pytest.mark.asyncio
    async def test_calculate_energy_cost(
        self,
        settings: SustainabilitySettings,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test calculating energy cost."""
        service = SustainabilityService(
            settings=settings,
            prometheus_client=mock_prometheus_client,
        )

        cost = await service.calculate_energy_cost()

        assert cost.energy_kwh == Decimal(1)  # 3600000 J = 1 kWh
        assert cost.price_per_kwh == Decimal("0.12")
        assert cost.total_cost == Decimal("0.12")
        assert cost.currency == "USD"

    @pytest.mark.asyncio
    async def test_get_cost_savings(
        self,
        settings: SustainabilitySettings,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test calculating cost savings."""
        service = SustainabilityService(
            settings=settings,
            prometheus_client=mock_prometheus_client,
        )

        savings = await service.get_cost_savings(
            namespace="default",
            baseline_cost=Decimal("1.00"),
        )

        # Current cost is 0.12, baseline is 1.00, savings = 0.88
        assert savings == Decimal("0.88")


class TestSustainabilityServiceReports:
    """Tests for SustainabilityService report methods."""

    @pytest.mark.asyncio
    async def test_generate_report(
        self,
        settings: SustainabilitySettings,
        mock_carbon_client: AsyncMock,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test generating sustainability report."""
        service = SustainabilityService(
            settings=settings,
            carbon_client=mock_carbon_client,
            prometheus_client=mock_prometheus_client,
        )

        now = datetime.now()
        report = await service.generate_report(
            namespace="default",
            period_start=now - timedelta(days=1),
            period_end=now,
        )

        assert report.namespace == "default"
        assert report.total_energy_kwh == Decimal(1)
        assert report.total_emissions_gco2 == Decimal(400)
        assert report.currency == "USD"

    @pytest.mark.asyncio
    async def test_get_progress(
        self,
        settings: SustainabilitySettings,
        mock_carbon_client: AsyncMock,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test calculating progress towards target."""
        service = SustainabilityService(
            settings=settings,
            carbon_client=mock_carbon_client,
            prometheus_client=mock_prometheus_client,
        )

        progress = await service.get_progress(
            namespace="default",
            baseline=Decimal(1000),
            target=Decimal(500),
        )

        # Current is 400, baseline 1000, target 500
        # Reduction = 1000 - 400 = 600
        # Target reduction = 1000 - 500 = 500
        # Progress = 600/500 * 100 = 120%
        assert progress == Decimal(120)

    @pytest.mark.asyncio
    async def test_get_trend(
        self,
        settings: SustainabilitySettings,
        mock_carbon_client: AsyncMock,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test calculating emission trend."""
        service = SustainabilityService(
            settings=settings,
            carbon_client=mock_carbon_client,
            prometheus_client=mock_prometheus_client,
        )

        trend = await service.get_trend(
            namespace="default",
            previous_emissions=Decimal(500),
        )

        # Current is 400, previous 500
        # Trend = (400 - 500) / 500 * 100 = -20%
        assert trend == Decimal(-20)


class TestSustainabilityServiceExport:
    """Tests for SustainabilityService export methods."""

    def test_export_metrics_csv(self, settings: SustainabilitySettings) -> None:
        """Test exporting metrics to CSV."""
        service = SustainabilityService(settings=settings)
        intensity = CarbonIntensity(
            region="us-east-1",
            intensity_gco2_per_kwh=Decimal(400),
            timestamp=datetime.now(),
            source="test",
            is_default=False,
        )
        metrics = [
            CarbonMetric(
                namespace="default",
                pod="api-pod",
                container="main",
                energy_kwh=Decimal(1),
                carbon_intensity=intensity,
                emissions_gco2=Decimal(400),
                timestamp=datetime.now(),
                confidence_lower=Decimal(360),
                confidence_upper=Decimal(440),
            )
        ]

        csv_output = service.export_metrics_csv(metrics)

        assert "namespace" in csv_output
        assert "default" in csv_output

    def test_export_metrics_json(self, settings: SustainabilitySettings) -> None:
        """Test exporting metrics to JSON."""
        service = SustainabilityService(settings=settings)
        intensity = CarbonIntensity(
            region="us-east-1",
            intensity_gco2_per_kwh=Decimal(400),
            timestamp=datetime.now(),
            source="test",
            is_default=False,
        )
        metrics = [
            CarbonMetric(
                namespace="default",
                pod="api-pod",
                container="main",
                energy_kwh=Decimal(1),
                carbon_intensity=intensity,
                emissions_gco2=Decimal(400),
                timestamp=datetime.now(),
                confidence_lower=Decimal(360),
                confidence_upper=Decimal(440),
            )
        ]

        json_output = service.export_metrics_json(metrics)

        assert "default" in json_output
        assert "400" in json_output


class TestSustainabilityServiceClose:
    """Tests for SustainabilityService close method."""

    @pytest.mark.asyncio
    async def test_close_with_clients(
        self,
        settings: SustainabilitySettings,
        mock_carbon_client: AsyncMock,
        mock_prometheus_client: AsyncMock,
    ) -> None:
        """Test closing service closes all clients."""
        service = SustainabilityService(
            settings=settings,
            carbon_client=mock_carbon_client,
            prometheus_client=mock_prometheus_client,
        )

        await service.close()

        mock_carbon_client.close.assert_called_once()
        mock_prometheus_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_clients(self, settings: SustainabilitySettings) -> None:
        """Test closing service without initialized clients."""
        service = SustainabilityService(settings=settings)

        # Should not raise
        await service.close()
