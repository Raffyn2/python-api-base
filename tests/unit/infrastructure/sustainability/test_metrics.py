"""Unit tests for sustainability metrics module."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.infrastructure.sustainability.metrics import (
    format_prometheus_metric,
    generate_metrics_output,
    record_carbon_intensity,
    record_carbon_metric,
    record_efficiency_metric,
    record_energy_cost,
    record_energy_metric,
    record_goal_progress,
    record_report_generated,
    validate_metric_labels,
)


class TestFormatPrometheusMetric:
    """Tests for format_prometheus_metric function."""

    def test_format_basic_metric(self) -> None:
        """Test formatting a basic metric."""
        result = format_prometheus_metric(
            name="test_metric",
            value=Decimal("42.5"),
            labels={"namespace": "test"},
        )

        assert "# TYPE test_metric gauge" in result
        assert 'test_metric{namespace="test"} 42.5' in result

    def test_format_metric_with_help_text(self) -> None:
        """Test formatting metric with help text."""
        result = format_prometheus_metric(
            name="energy_consumption",
            value=100.0,
            labels={"namespace": "prod"},
            help_text="Total energy consumption",
        )

        assert "# HELP energy_consumption Total energy consumption" in result
        assert "# TYPE energy_consumption gauge" in result

    def test_format_metric_with_multiple_labels(self) -> None:
        """Test formatting metric with multiple labels."""
        result = format_prometheus_metric(
            name="carbon_emissions",
            value=Decimal(500),
            labels={"namespace": "prod", "pod": "api-1", "container": "main"},
        )

        assert 'container="main"' in result
        assert 'namespace="prod"' in result
        assert 'pod="api-1"' in result

    def test_format_counter_metric(self) -> None:
        """Test formatting counter metric type."""
        result = format_prometheus_metric(
            name="requests_total",
            value=1000,
            labels={"namespace": "test"},
            metric_type="counter",
        )

        assert "# TYPE requests_total counter" in result

    def test_format_histogram_metric(self) -> None:
        """Test formatting histogram metric type."""
        result = format_prometheus_metric(
            name="request_duration",
            value=0.5,
            labels={"namespace": "test"},
            metric_type="histogram",
        )

        assert "# TYPE request_duration histogram" in result


class TestValidateMetricLabels:
    """Tests for validate_metric_labels function."""

    def test_validate_labels_with_namespace(self) -> None:
        """Test validation passes with namespace label."""
        labels = {"namespace": "production"}
        assert validate_metric_labels(labels) is True

    def test_validate_labels_with_all_required(self) -> None:
        """Test validation passes with all labels."""
        labels = {"namespace": "prod", "pod": "api-1", "container": "main"}
        assert validate_metric_labels(labels) is True

    def test_validate_labels_missing_namespace(self) -> None:
        """Test validation fails without namespace."""
        labels = {"pod": "api-1", "container": "main"}
        assert validate_metric_labels(labels) is False

    def test_validate_labels_empty(self) -> None:
        """Test validation fails with empty labels."""
        assert validate_metric_labels({}) is False


class TestGenerateMetricsOutput:
    """Tests for generate_metrics_output function."""

    def test_generate_single_metric(self) -> None:
        """Test generating output for single metric."""
        metrics = [
            {
                "name": "test_metric",
                "value": 100,
                "labels": {"namespace": "test"},
            }
        ]

        result = generate_metrics_output(metrics)

        assert "test_metric" in result
        assert "100" in result

    def test_generate_multiple_metrics(self) -> None:
        """Test generating output for multiple metrics."""
        metrics = [
            {"name": "metric_a", "value": 10, "labels": {"namespace": "a"}},
            {"name": "metric_b", "value": 20, "labels": {"namespace": "b"}},
        ]

        result = generate_metrics_output(metrics)

        assert "metric_a" in result
        assert "metric_b" in result

    def test_generate_metrics_with_help(self) -> None:
        """Test generating output with help text."""
        metrics = [
            {
                "name": "energy_total",
                "value": 500,
                "labels": {"namespace": "prod"},
                "help": "Total energy consumption",
            }
        ]

        result = generate_metrics_output(metrics)

        assert "# HELP energy_total Total energy consumption" in result

    def test_generate_empty_metrics(self) -> None:
        """Test generating output for empty list."""
        result = generate_metrics_output([])
        assert result == ""


class TestRecordMetricFunctions:
    """Tests for metric recording functions."""

    @patch("src.infrastructure.sustainability.metrics.ENERGY_CONSUMPTION_TOTAL")
    @patch("src.infrastructure.sustainability.metrics.ENERGY_CONSUMPTION_KWH")
    def test_record_energy_metric(self, mock_kwh: MagicMock, mock_total: MagicMock) -> None:
        """Test recording energy metric."""
        mock_total.labels.return_value.inc = MagicMock()
        mock_kwh.labels.return_value.set = MagicMock()

        record_energy_metric(
            namespace="test",
            pod="pod-1",
            container="main",
            energy_joules=Decimal(3600000),  # 1 kWh
        )

        mock_total.labels.assert_called_with(namespace="test", pod="pod-1", container="main")
        mock_kwh.labels.assert_called_with(namespace="test", pod="pod-1", container="main")

    @patch("src.infrastructure.sustainability.metrics.CARBON_EMISSIONS_TOTAL")
    @patch("src.infrastructure.sustainability.metrics.CARBON_EMISSIONS_RATE")
    def test_record_carbon_metric(self, mock_rate: MagicMock, mock_total: MagicMock) -> None:
        """Test recording carbon metric."""
        mock_total.labels.return_value.inc = MagicMock()
        mock_rate.labels.return_value.set = MagicMock()

        record_carbon_metric(
            namespace="test",
            pod="pod-1",
            container="main",
            emissions_gco2=Decimal(400),
        )

        mock_total.labels.assert_called_with(namespace="test", pod="pod-1", container="main")

    @patch("src.infrastructure.sustainability.metrics.CARBON_INTENSITY")
    def test_record_carbon_intensity(self, mock_intensity: MagicMock) -> None:
        """Test recording carbon intensity metric."""
        mock_intensity.labels.return_value.set = MagicMock()

        record_carbon_intensity(
            region="us-east-1",
            source="electricity-maps",
            intensity_gco2_per_kwh=Decimal(350),
        )

        mock_intensity.labels.assert_called_with(region="us-east-1", source="electricity-maps")

    @patch("src.infrastructure.sustainability.metrics.ENERGY_COST_TOTAL")
    @patch("src.infrastructure.sustainability.metrics.ENERGY_COST_RATE")
    def test_record_energy_cost(self, mock_rate: MagicMock, mock_total: MagicMock) -> None:
        """Test recording energy cost metric."""
        mock_total.labels.return_value.inc = MagicMock()
        mock_rate.labels.return_value.set = MagicMock()

        record_energy_cost(
            namespace="production",
            currency="USD",
            cost=Decimal("12.50"),
        )

        mock_total.labels.assert_called_with(namespace="production", currency="USD")

    @patch("src.infrastructure.sustainability.metrics.ENERGY_PER_REQUEST")
    def test_record_efficiency_metric(self, mock_histogram: MagicMock) -> None:
        """Test recording efficiency metric."""
        mock_histogram.labels.return_value.observe = MagicMock()

        record_efficiency_metric(
            namespace="prod",
            deployment="api",
            energy_per_request=Decimal("0.5"),
        )

        mock_histogram.labels.assert_called_with(namespace="prod", deployment="api")

    @patch("src.infrastructure.sustainability.metrics.GOAL_PROGRESS_PERCENTAGE")
    def test_record_goal_progress(self, mock_gauge: MagicMock) -> None:
        """Test recording goal progress metric."""
        mock_gauge.labels.return_value.set = MagicMock()

        record_goal_progress(namespace="prod", progress_percentage=Decimal("75.5"))

        mock_gauge.labels.assert_called_with(namespace="prod")

    @patch("src.infrastructure.sustainability.metrics.SUSTAINABILITY_REPORT_GENERATED")
    def test_record_report_generated(self, mock_counter: MagicMock) -> None:
        """Test recording report generated metric."""
        mock_counter.labels.return_value.inc = MagicMock()

        record_report_generated(namespace="production")

        mock_counter.labels.assert_called_with(namespace="production")
