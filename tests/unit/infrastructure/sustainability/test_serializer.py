"""Unit tests for sustainability serializer module."""

import json
from datetime import datetime
from decimal import Decimal

import pytest

from src.infrastructure.sustainability.models import CarbonIntensity, CarbonMetric, EnergyMetric
from src.infrastructure.sustainability.serializer import (
    ValidationError,
    deserialize_carbon_metric,
    deserialize_carbon_metric_from_json,
    export_to_csv,
    export_to_json,
    serialize_carbon_metric,
    serialize_carbon_metric_to_json,
)


@pytest.fixture
def sample_carbon_metric():
    """Create a sample carbon metric for testing."""
    energy = EnergyMetric(
        namespace="default",
        pod="my-pod",
        container="app",
        energy_joules=Decimal("3600000"),
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        source="rapl",
    )
    intensity = CarbonIntensity(
        region="US",
        intensity_gco2_per_kwh=Decimal("400"),
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        source="default",
    )
    return CarbonMetric.calculate(energy, intensity)


class TestSerializeCarbonMetric:
    """Tests for serialize_carbon_metric function."""

    def test_serialization(self, sample_carbon_metric):
        """Test basic serialization."""
        result = serialize_carbon_metric(sample_carbon_metric)
        
        assert result["namespace"] == "default"
        assert result["pod"] == "my-pod"
        assert result["emissions_gco2"] == "400"
        assert "carbon_intensity" in result

    def test_json_serialization(self, sample_carbon_metric):
        """Test JSON string serialization."""
        result = serialize_carbon_metric_to_json(sample_carbon_metric)
        
        parsed = json.loads(result)
        assert parsed["namespace"] == "default"


class TestDeserializeCarbonMetric:
    """Tests for deserialize_carbon_metric function."""

    def test_deserialization(self, sample_carbon_metric):
        """Test basic deserialization."""
        serialized = serialize_carbon_metric(sample_carbon_metric)
        result = deserialize_carbon_metric(serialized)
        
        assert result.namespace == sample_carbon_metric.namespace
        assert result.emissions_gco2 == sample_carbon_metric.emissions_gco2

    def test_missing_field_raises_error(self):
        """Test missing required field raises ValidationError."""
        with pytest.raises(ValidationError, match="Missing required field"):
            deserialize_carbon_metric({"namespace": "test"})


class TestDeserializeFromJson:
    """Tests for deserialize_carbon_metric_from_json function."""

    def test_invalid_json_raises_error(self):
        """Test invalid JSON raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid JSON"):
            deserialize_carbon_metric_from_json("not json")

    def test_non_object_raises_error(self):
        """Test non-object JSON raises ValidationError."""
        with pytest.raises(ValidationError, match="must be an object"):
            deserialize_carbon_metric_from_json("[]")


class TestExportToCsv:
    """Tests for export_to_csv function."""

    def test_csv_export(self, sample_carbon_metric):
        """Test CSV export."""
        result = export_to_csv([sample_carbon_metric])
        
        lines = result.strip().split("\n")
        assert len(lines) == 2  # Header + 1 row
        assert "namespace" in lines[0]
        assert "default" in lines[1]

    def test_empty_list(self):
        """Test CSV export with empty list."""
        result = export_to_csv([])
        
        lines = result.strip().split("\n")
        assert len(lines) == 1  # Header only


class TestExportToJson:
    """Tests for export_to_json function."""

    def test_json_export(self, sample_carbon_metric):
        """Test JSON export."""
        result = export_to_json([sample_carbon_metric])
        
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["namespace"] == "default"
