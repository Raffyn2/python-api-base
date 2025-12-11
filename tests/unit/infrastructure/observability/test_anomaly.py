"""Tests for anomaly detection module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.3**
"""

from datetime import UTC, datetime

import pytest

from infrastructure.observability.anomaly import (
    Anomaly,
    AnomalyConfig,
    AnomalyDetector,
    AnomalySeverity,
    AnomalyType,
    DataPoint,
    LogAnomalyHandler,
    StatisticalAnalyzer,
    create_anomaly_detector,
)


class TestAnomalyType:
    """Tests for AnomalyType enum."""

    def test_spike_value(self) -> None:
        """Test SPIKE type value."""
        assert AnomalyType.SPIKE.value == "spike"

    def test_drop_value(self) -> None:
        """Test DROP type value."""
        assert AnomalyType.DROP.value == "drop"

    def test_trend_up_value(self) -> None:
        """Test TREND_UP type value."""
        assert AnomalyType.TREND_UP.value == "trend_up"

    def test_trend_down_value(self) -> None:
        """Test TREND_DOWN type value."""
        assert AnomalyType.TREND_DOWN.value == "trend_down"

    def test_outlier_value(self) -> None:
        """Test OUTLIER type value."""
        assert AnomalyType.OUTLIER.value == "outlier"


class TestAnomalySeverity:
    """Tests for AnomalySeverity enum."""

    def test_info_value(self) -> None:
        """Test INFO severity value."""
        assert AnomalySeverity.INFO.value == "info"

    def test_warning_value(self) -> None:
        """Test WARNING severity value."""
        assert AnomalySeverity.WARNING.value == "warning"

    def test_critical_value(self) -> None:
        """Test CRITICAL severity value."""
        assert AnomalySeverity.CRITICAL.value == "critical"


class TestDataPoint:
    """Tests for DataPoint."""

    def test_create_data_point(self) -> None:
        """Test creating a data point."""
        now = datetime.now(UTC)
        point = DataPoint(value=100.0, timestamp=now)
        assert point.value == 100.0
        assert point.timestamp == now
        assert point.labels == {}

    def test_create_with_labels(self) -> None:
        """Test creating data point with labels."""
        now = datetime.now(UTC)
        labels = {"service": "api", "endpoint": "/users"}
        point = DataPoint(value=50.0, timestamp=now, labels=labels)
        assert point.labels == labels

    def test_frozen_dataclass(self) -> None:
        """Test that DataPoint is immutable."""
        point = DataPoint(value=100.0, timestamp=datetime.now(UTC))
        with pytest.raises(AttributeError):
            point.value = 200.0


class TestAnomaly:
    """Tests for Anomaly."""

    def test_create_anomaly(self) -> None:
        """Test creating an anomaly."""
        now = datetime.now(UTC)
        anomaly = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            severity=AnomalySeverity.WARNING,
            value=150.0,
            expected_value=100.0,
            deviation=2.5,
            timestamp=now,
            metric_name="request_count",
        )
        assert anomaly.anomaly_type == AnomalyType.SPIKE
        assert anomaly.severity == AnomalySeverity.WARNING
        assert anomaly.value == 150.0
        assert anomaly.expected_value == 100.0

    def test_deviation_percent(self) -> None:
        """Test deviation percentage calculation."""
        anomaly = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            severity=AnomalySeverity.WARNING,
            value=150.0,
            expected_value=100.0,
            deviation=2.5,
            timestamp=datetime.now(UTC),
            metric_name="test",
        )
        assert anomaly.deviation_percent == 50.0

    def test_deviation_percent_zero_expected(self) -> None:
        """Test deviation percentage when expected is zero."""
        anomaly = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            severity=AnomalySeverity.WARNING,
            value=100.0,
            expected_value=0.0,
            deviation=2.5,
            timestamp=datetime.now(UTC),
            metric_name="test",
        )
        assert anomaly.deviation_percent == 100.0

    def test_deviation_percent_both_zero(self) -> None:
        """Test deviation percentage when both are zero."""
        anomaly = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            severity=AnomalySeverity.INFO,
            value=0.0,
            expected_value=0.0,
            deviation=0.0,
            timestamp=datetime.now(UTC),
            metric_name="test",
        )
        assert anomaly.deviation_percent == 0.0


class TestAnomalyConfig:
    """Tests for AnomalyConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = AnomalyConfig()
        assert config.z_score_threshold == 3.0
        assert config.min_data_points == 10
        assert config.window_size == 20
        assert config.spike_threshold == 2.5
        assert config.trend_window == 10
        assert config.trend_threshold == 0.1
        assert config.warning_threshold == 2.0
        assert config.critical_threshold == 3.0

    def test_custom_z_score_threshold(self) -> None:
        """Test custom z-score threshold."""
        config = AnomalyConfig(z_score_threshold=2.5)
        assert config.z_score_threshold == 2.5

    def test_custom_min_data_points(self) -> None:
        """Test custom minimum data points."""
        config = AnomalyConfig(min_data_points=20)
        assert config.min_data_points == 20


class TestStatisticalAnalyzer:
    """Tests for StatisticalAnalyzer."""

    def test_mean_empty_list(self) -> None:
        """Test mean of empty list."""
        assert StatisticalAnalyzer.mean([]) == 0.0

    def test_mean_single_value(self) -> None:
        """Test mean of single value."""
        assert StatisticalAnalyzer.mean([5.0]) == 5.0

    def test_mean_multiple_values(self) -> None:
        """Test mean of multiple values."""
        assert StatisticalAnalyzer.mean([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.0

    def test_std_dev_empty_list(self) -> None:
        """Test std dev of empty list."""
        assert StatisticalAnalyzer.std_dev([]) == 0.0

    def test_std_dev_single_value(self) -> None:
        """Test std dev of single value."""
        assert StatisticalAnalyzer.std_dev([5.0]) == 0.0

    def test_std_dev_multiple_values(self) -> None:
        """Test std dev of multiple values."""
        std = StatisticalAnalyzer.std_dev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
        assert abs(std - 2.138) < 0.01

    def test_z_score_zero_std_dev(self) -> None:
        """Test z-score with zero std dev."""
        assert StatisticalAnalyzer.z_score(5.0, 5.0, 0.0) == 0.0

    def test_z_score_positive(self) -> None:
        """Test positive z-score."""
        z = StatisticalAnalyzer.z_score(7.0, 5.0, 1.0)
        assert z == 2.0

    def test_z_score_negative(self) -> None:
        """Test negative z-score."""
        z = StatisticalAnalyzer.z_score(3.0, 5.0, 1.0)
        assert z == -2.0

    def test_moving_average_short_list(self) -> None:
        """Test moving average with list shorter than window."""
        result = StatisticalAnalyzer.moving_average([1.0, 2.0, 3.0], 5)
        assert len(result) == 3
        assert all(v == 2.0 for v in result)

    def test_moving_average(self) -> None:
        """Test moving average calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = StatisticalAnalyzer.moving_average(values, 3)
        assert len(result) == 5
        assert result[-1] == 4.0  # Average of 3, 4, 5

    def test_linear_regression_slope_empty(self) -> None:
        """Test slope with empty list."""
        assert StatisticalAnalyzer.linear_regression_slope([]) == 0.0

    def test_linear_regression_slope_single(self) -> None:
        """Test slope with single value."""
        assert StatisticalAnalyzer.linear_regression_slope([5.0]) == 0.0

    def test_linear_regression_slope_increasing(self) -> None:
        """Test slope with increasing values."""
        slope = StatisticalAnalyzer.linear_regression_slope([1.0, 2.0, 3.0, 4.0, 5.0])
        assert slope == 1.0

    def test_linear_regression_slope_decreasing(self) -> None:
        """Test slope with decreasing values."""
        slope = StatisticalAnalyzer.linear_regression_slope([5.0, 4.0, 3.0, 2.0, 1.0])
        assert slope == -1.0

    def test_percentile_empty(self) -> None:
        """Test percentile of empty list."""
        assert StatisticalAnalyzer.percentile([], 0.5) == 0.0

    def test_percentile_50(self) -> None:
        """Test 50th percentile (median)."""
        p50 = StatisticalAnalyzer.percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5)
        assert p50 == 3.0

    def test_percentile_95(self) -> None:
        """Test 95th percentile."""
        values = list(range(1, 101))
        p95 = StatisticalAnalyzer.percentile([float(v) for v in values], 0.95)
        # Implementation uses int(len * p) which gives index 95 -> value 96
        assert p95 == 96.0


class TestAnomalyDetector:
    """Tests for AnomalyDetector."""

    @pytest.mark.asyncio
    async def test_record_first_point(self) -> None:
        """Test recording first data point."""
        detector = AnomalyDetector()
        anomaly = await detector.record("test_metric", 100.0)
        assert anomaly is None  # Not enough data

    @pytest.mark.asyncio
    async def test_record_with_labels(self) -> None:
        """Test recording with labels."""
        detector = AnomalyDetector()
        labels = {"service": "api"}
        anomaly = await detector.record("test_metric", 100.0, labels=labels)
        assert anomaly is None

    @pytest.mark.asyncio
    async def test_detect_spike(self) -> None:
        """Test detecting a spike anomaly."""
        config = AnomalyConfig(min_data_points=5, z_score_threshold=2.0)
        detector = AnomalyDetector(config=config)

        # Record normal values with some variation to get non-zero std dev
        for i in range(10):
            await detector.record("test", 100.0 + (i * 0.1))

        # Record spike - much higher than normal
        anomaly = await detector.record("test", 1000.0)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.SPIKE

    @pytest.mark.asyncio
    async def test_detect_drop(self) -> None:
        """Test detecting a drop anomaly."""
        config = AnomalyConfig(min_data_points=5, z_score_threshold=2.0)
        detector = AnomalyDetector(config=config)

        # Record normal values with some variation to get non-zero std dev
        for i in range(10):
            await detector.record("test", 100.0 + (i * 0.1))

        # Record drop - much lower than normal
        anomaly = await detector.record("test", 0.0)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.DROP

    @pytest.mark.asyncio
    async def test_no_anomaly_normal_values(self) -> None:
        """Test no anomaly with normal values."""
        config = AnomalyConfig(min_data_points=5)
        detector = AnomalyDetector(config=config)

        # Record normal values with small variation
        for i in range(15):
            anomaly = await detector.record("test", 100.0 + (i % 3))
            if i >= 5:
                assert anomaly is None

    def test_get_statistics_empty(self) -> None:
        """Test getting statistics for empty metric."""
        detector = AnomalyDetector()
        stats = detector.get_statistics("nonexistent")
        assert stats["count"] == 0
        assert stats["mean"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics(self) -> None:
        """Test getting statistics for metric."""
        detector = AnomalyDetector()
        for i in range(10):
            await detector.record("test", float(i + 1))

        stats = detector.get_statistics("test")
        assert stats["count"] == 10
        assert stats["mean"] == 5.5
        assert stats["min"] == 1.0
        assert stats["max"] == 10.0

    def test_determine_severity_critical(self) -> None:
        """Test critical severity determination."""
        config = AnomalyConfig(critical_threshold=3.0)
        detector = AnomalyDetector(config=config)
        severity = detector._determine_severity(4.0)
        assert severity == AnomalySeverity.CRITICAL

    def test_determine_severity_warning(self) -> None:
        """Test warning severity determination."""
        config = AnomalyConfig(warning_threshold=2.0, critical_threshold=3.0)
        detector = AnomalyDetector(config=config)
        severity = detector._determine_severity(2.5)
        assert severity == AnomalySeverity.WARNING

    def test_determine_severity_info(self) -> None:
        """Test info severity determination."""
        config = AnomalyConfig(warning_threshold=2.0)
        detector = AnomalyDetector(config=config)
        severity = detector._determine_severity(1.5)
        assert severity == AnomalySeverity.INFO


class TestLogAnomalyHandler:
    """Tests for LogAnomalyHandler."""

    @pytest.mark.asyncio
    async def test_handle_logs_anomaly(self) -> None:
        """Test that handler logs anomaly."""
        handler = LogAnomalyHandler()
        anomaly = Anomaly(
            anomaly_type=AnomalyType.SPIKE,
            severity=AnomalySeverity.WARNING,
            value=150.0,
            expected_value=100.0,
            deviation=2.5,
            timestamp=datetime.now(UTC),
            metric_name="test_metric",
        )
        # Should not raise
        await handler.handle(anomaly)


class TestCreateAnomalyDetector:
    """Tests for create_anomaly_detector factory."""

    def test_create_with_defaults(self) -> None:
        """Test creating detector with defaults."""
        detector = create_anomaly_detector()
        assert isinstance(detector, AnomalyDetector)

    def test_create_with_custom_config(self) -> None:
        """Test creating detector with custom config."""
        config = AnomalyConfig(z_score_threshold=2.5)
        detector = create_anomaly_detector(config=config)
        assert detector._config.z_score_threshold == 2.5

    def test_create_with_custom_handler(self) -> None:
        """Test creating detector with custom handler."""
        handler = LogAnomalyHandler()
        detector = create_anomaly_detector(handler=handler)
        assert detector._handler is handler
