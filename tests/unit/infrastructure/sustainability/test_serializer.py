"""Tests for sustainability serializer module.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

import json
from datetime import datetime
from decimal import Decimal

import pytest

from infrastructure.sustainability.models import CarbonIntensity, CarbonMetric
from infrastructure.sustainability.serializer import (
    DecimalEncoder,
    ValidationError,
    deserialize_carbon_intensity,
    deserialize_carbon_metric,
    deserialize_carbon_metric_from_json,
    export_to_csv,
    export_to_json,
    parse_csv,
    serialize_carbon_intensity,
    serialize_carbon_metric,
    serialize_carbon_metric_to_json,
    validate_json,
)


@pytest.fixture
def sample_intensity() -> CarbonIntensity:
    """Create a sample CarbonIntensity."""
    return CarbonIntensity(
        region="us-west",
        intensity_gco2_per_kwh=Decimal("400"),
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        source="test",
    )


@pytest.fixture
def sample_metric(sample_intensity: CarbonIntensity) -> CarbonMetric:
    """Create a sample CarbonMetric."""
    return CarbonMetric(
        namespace="default",
        pod="test-pod",
        container="test-container",
        energy_kwh=Decimal("1.5"),
        carbon_intensity=sample_intensity,
        emissions_gco2=Decimal("600"),
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        confidence_lower=Decimal("540"),
        confidence_upper=Decimal("660"),
    )


class TestDecimalEncoder:
    """Tests for DecimalEncoder."""

    def test_encode_decimal(self) -> None:
        """Test encoding Decimal values."""
        data = {"value": Decimal("123.45")}
        result = json.dumps(data, cls=DecimalEncoder)
        assert '"123.45"' in result

    def test_encode_datetime(self) -> None:
        """Test encoding datetime values."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        data = {"timestamp": dt}
        result = json.dumps(data, cls=DecimalEncoder)
        assert "2024-01-15T10:30:00" in result

    def test_encode_regular_types(self) -> None:
        """Test encoding regular types."""
        data = {"string": "test", "number": 42, "bool": True}
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        assert parsed["string"] == "test"
        assert parsed["number"] == 42
        assert parsed["bool"] is True


class TestSerializeCarbonIntensity:
    """Tests for serialize_carbon_intensity."""

    def test_serialize(self, sample_intensity: CarbonIntensity) -> None:
        """Test serialization."""
        result = serialize_carbon_intensity(sample_intensity)
        assert result["region"] == "us-west"
        assert result["intensity_gco2_per_kwh"] == "400"
        assert result["source"] == "test"
        assert result["is_default"] is False

    def test_serialize_with_default_flag(self) -> None:
        """Test serialization with is_default=True."""
        intensity = CarbonIntensity(
            region="global",
            intensity_gco2_per_kwh=Decimal("500"),
            timestamp=datetime.now(),
            source="default",
            is_default=True,
        )
        result = serialize_carbon_intensity(intensity)
        assert result["is_default"] is True


class TestDeserializeCarbonIntensity:
    """Tests for deserialize_carbon_intensity."""

    def test_deserialize(self) -> None:
        """Test deserialization."""
        data = {
            "region": "eu-central",
            "intensity_gco2_per_kwh": "350",
            "timestamp": "2024-01-15T10:30:00",
            "source": "api",
            "is_default": False,
        }
        result = deserialize_carbon_intensity(data)
        assert result.region == "eu-central"
        assert result.intensity_gco2_per_kwh == Decimal("350")
        assert result.source == "api"

    def test_deserialize_without_is_default(self) -> None:
        """Test deserialization without is_default field."""
        data = {
            "region": "us-east",
            "intensity_gco2_per_kwh": "400",
            "timestamp": "2024-01-15T10:30:00",
            "source": "test",
        }
        result = deserialize_carbon_intensity(data)
        assert result.is_default is False


class TestSerializeCarbonMetric:
    """Tests for serialize_carbon_metric."""

    def test_serialize(self, sample_metric: CarbonMetric) -> None:
        """Test serialization."""
        result = serialize_carbon_metric(sample_metric)
        assert result["namespace"] == "default"
        assert result["pod"] == "test-pod"
        assert result["container"] == "test-container"
        assert result["energy_kwh"] == "1.5"
        assert result["emissions_gco2"] == "600"
        assert "carbon_intensity" in result


class TestDeserializeCarbonMetric:
    """Tests for deserialize_carbon_metric."""

    def test_deserialize(self, sample_metric: CarbonMetric) -> None:
        """Test deserialization."""
        data = serialize_carbon_metric(sample_metric)
        result = deserialize_carbon_metric(data)
        assert result.namespace == sample_metric.namespace
        assert result.pod == sample_metric.pod
        assert result.emissions_gco2 == sample_metric.emissions_gco2

    def test_missing_field_raises(self) -> None:
        """Test that missing field raises ValidationError."""
        data = {"namespace": "test"}
        with pytest.raises(ValidationError, match="Missing required field"):
            deserialize_carbon_metric(data)


class TestSerializeCarbonMetricToJson:
    """Tests for serialize_carbon_metric_to_json."""

    def test_serialize_to_json(self, sample_metric: CarbonMetric) -> None:
        """Test JSON serialization."""
        result = serialize_carbon_metric_to_json(sample_metric)
        parsed = json.loads(result)
        assert parsed["namespace"] == "default"
        assert parsed["pod"] == "test-pod"


class TestDeserializeCarbonMetricFromJson:
    """Tests for deserialize_carbon_metric_from_json."""

    def test_deserialize_from_json(self, sample_metric: CarbonMetric) -> None:
        """Test JSON deserialization."""
        json_str = serialize_carbon_metric_to_json(sample_metric)
        result = deserialize_carbon_metric_from_json(json_str)
        assert result.namespace == sample_metric.namespace
        assert result.pod == sample_metric.pod

    def test_invalid_json_raises(self) -> None:
        """Test that invalid JSON raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid JSON"):
            deserialize_carbon_metric_from_json("not valid json")

    def test_non_object_json_raises(self) -> None:
        """Test that non-object JSON raises ValidationError."""
        with pytest.raises(ValidationError, match="JSON must be an object"):
            deserialize_carbon_metric_from_json("[1, 2, 3]")


class TestExportToCsv:
    """Tests for export_to_csv."""

    def test_export_empty_list(self) -> None:
        """Test exporting empty list."""
        result = export_to_csv([])
        assert "namespace" in result  # Headers should be present
        lines = result.strip().split("\n")
        assert len(lines) == 1  # Only headers

    def test_export_single_metric(self, sample_metric: CarbonMetric) -> None:
        """Test exporting single metric."""
        result = export_to_csv([sample_metric])
        lines = result.strip().split("\n")
        assert len(lines) == 2  # Headers + 1 data row
        assert "default" in lines[1]
        assert "test-pod" in lines[1]

    def test_export_multiple_metrics(
        self, sample_metric: CarbonMetric, sample_intensity: CarbonIntensity
    ) -> None:
        """Test exporting multiple metrics."""
        metric2 = CarbonMetric(
            namespace="production",
            pod="prod-pod",
            container="prod-container",
            energy_kwh=Decimal("2.5"),
            carbon_intensity=sample_intensity,
            emissions_gco2=Decimal("1000"),
            timestamp=datetime.now(),
            confidence_lower=Decimal("900"),
            confidence_upper=Decimal("1100"),
        )
        result = export_to_csv([sample_metric, metric2])
        lines = result.strip().split("\n")
        assert len(lines) == 3  # Headers + 2 data rows


class TestExportToJson:
    """Tests for export_to_json."""

    def test_export_empty_list(self) -> None:
        """Test exporting empty list."""
        result = export_to_json([])
        assert result == "[]"

    def test_export_single_metric(self, sample_metric: CarbonMetric) -> None:
        """Test exporting single metric."""
        result = export_to_json([sample_metric])
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["namespace"] == "default"

    def test_export_produces_valid_json(self, sample_metric: CarbonMetric) -> None:
        """Test that export produces valid JSON."""
        result = export_to_json([sample_metric])
        assert validate_json(result)


class TestParseCsv:
    """Tests for parse_csv."""

    def test_parse_csv(self) -> None:
        """Test parsing CSV content."""
        csv_content = "name,value\ntest,123\nother,456"
        result = parse_csv(csv_content)
        assert len(result) == 2
        assert result[0]["name"] == "test"
        assert result[0]["value"] == "123"

    def test_parse_empty_csv(self) -> None:
        """Test parsing empty CSV."""
        csv_content = "name,value"
        result = parse_csv(csv_content)
        assert len(result) == 0


class TestValidateJson:
    """Tests for validate_json."""

    def test_valid_json(self) -> None:
        """Test valid JSON."""
        assert validate_json('{"key": "value"}') is True
        assert validate_json("[1, 2, 3]") is True
        assert validate_json('"string"') is True

    def test_invalid_json(self) -> None:
        """Test invalid JSON."""
        assert validate_json("not json") is False
        assert validate_json("{invalid}") is False
        assert validate_json("") is False
