"""Unit tests for sustainability client module."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.sustainability.client import (
    CarbonIntensityClient,
    CircuitBreaker,
    CircuitState,
    PrometheusClient,
)
from src.infrastructure.sustainability.config import SustainabilitySettings


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_circuit_states_exist(self) -> None:
        """Test all circuit states are defined."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initial_state_is_closed(self) -> None:
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_record_success_resets_failures(self) -> None:
        """Test recording success resets failure count."""
        cb = CircuitBreaker()
        cb.failure_count = 3
        cb.state = CircuitState.HALF_OPEN

        cb.record_success()

        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_record_failure_increments_count(self) -> None:
        """Test recording failure increments count."""
        cb = CircuitBreaker(failure_threshold=5)

        cb.record_failure()

        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED

    def test_circuit_opens_after_threshold(self) -> None:
        """Test circuit opens after reaching failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_can_execute_when_closed(self) -> None:
        """Test can execute when circuit is closed."""
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_cannot_execute_when_open(self) -> None:
        """Test cannot execute when circuit is open."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        cb.record_failure()

        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_half_open_after_recovery_timeout(self) -> None:
        """Test circuit transitions to half-open after timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        cb.last_failure_time = datetime.now() - timedelta(seconds=1)

        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_execution(self) -> None:
        """Test half-open state allows execution."""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN

        assert cb.can_execute() is True


class TestCarbonIntensityClient:
    """Tests for CarbonIntensityClient class."""

    def test_client_initialization(self) -> None:
        """Test client initializes with settings."""
        settings = SustainabilitySettings()
        client = CarbonIntensityClient(settings)

        assert client.settings == settings
        assert client.circuit_breaker is not None

    def test_get_default_intensity(self) -> None:
        """Test getting default carbon intensity."""
        settings = SustainabilitySettings(
            default_region="us-east-1",
            default_carbon_intensity_gco2_per_kwh=Decimal(450),
        )
        client = CarbonIntensityClient(settings)

        intensity = client._get_default_intensity()

        assert intensity.region == "us-east-1"
        assert intensity.intensity_gco2_per_kwh == Decimal(450)
        assert intensity.is_default is True
        assert intensity.source == "default"

    @pytest.mark.asyncio
    async def test_get_carbon_intensity_circuit_open(self) -> None:
        """Test returns default when circuit is open."""
        settings = SustainabilitySettings()
        client = CarbonIntensityClient(settings)
        client.circuit_breaker.state = CircuitState.OPEN
        client.circuit_breaker.last_failure_time = datetime.now()

        intensity = await client.get_carbon_intensity("us-east-1")

        assert intensity.is_default is True

    @pytest.mark.asyncio
    async def test_get_carbon_intensity_api_failure(self) -> None:
        """Test returns default on API failure."""
        settings = SustainabilitySettings()
        client = CarbonIntensityClient(settings)

        with patch.object(client, "_fetch_intensity", side_effect=Exception("API Error")):
            intensity = await client.get_carbon_intensity("us-east-1")

        assert intensity.is_default is True
        assert client.circuit_breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_close_client(self) -> None:
        """Test closing the client."""
        settings = SustainabilitySettings()
        client = CarbonIntensityClient(settings)
        client._client = AsyncMock()

        await client.close()

        client._client.aclose.assert_called_once()


class TestPrometheusClient:
    """Tests for PrometheusClient class."""

    def test_client_initialization(self) -> None:
        """Test client initializes with settings."""
        settings = SustainabilitySettings(prometheus_url="http://localhost:9090")
        client = PrometheusClient(settings)

        assert client.settings == settings

    @pytest.mark.asyncio
    async def test_query_success(self) -> None:
        """Test successful Prometheus query."""
        settings = SustainabilitySettings()
        client = PrometheusClient(settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {"result": [{"metric": {}, "value": [1234567890, "100"]}]},
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.query("up")

            assert len(result) == 1
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_failure(self) -> None:
        """Test Prometheus query failure."""
        settings = SustainabilitySettings()
        client = PrometheusClient(settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "error",
            "error": "bad query",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="Prometheus query failed"):
                await client.query("invalid{")

    @pytest.mark.asyncio
    async def test_query_range_success(self) -> None:
        """Test successful Prometheus range query."""
        settings = SustainabilitySettings()
        client = PrometheusClient(settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {"result": []},
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            start = datetime.now() - timedelta(hours=1)
            end = datetime.now()
            result = await client.query_range("up", start, end)

            assert result == []

    @pytest.mark.asyncio
    async def test_get_kepler_energy_metrics(self) -> None:
        """Test fetching Kepler energy metrics."""
        settings = SustainabilitySettings()
        client = PrometheusClient(settings)

        mock_results = [
            {
                "metric": {
                    "namespace": "default",
                    "pod": "api-pod",
                    "container": "main",
                    "source": "rapl",
                },
                "value": [1234567890, "3600000"],
            }
        ]

        with patch.object(client, "query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_results

            metrics = await client.get_kepler_energy_metrics()

            assert len(metrics) == 1
            assert metrics[0].namespace == "default"
            assert metrics[0].energy_joules == Decimal(3600000)

    @pytest.mark.asyncio
    async def test_get_kepler_energy_metrics_with_namespace(self) -> None:
        """Test fetching Kepler metrics filtered by namespace."""
        settings = SustainabilitySettings()
        client = PrometheusClient(settings)

        with patch.object(client, "query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []

            await client.get_kepler_energy_metrics(namespace="production")

            call_args = mock_query.call_args[0][0]
            assert 'namespace="production"' in call_args

    @pytest.mark.asyncio
    async def test_close_client(self) -> None:
        """Test closing the client."""
        settings = SustainabilitySettings()
        client = PrometheusClient(settings)
        client._client = AsyncMock()

        await client.close()

        client._client.aclose.assert_called_once()
