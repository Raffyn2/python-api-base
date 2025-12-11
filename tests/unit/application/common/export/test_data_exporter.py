"""Unit tests for DataExporter.

Tests JSON, CSV, and JSONL export functionality.
"""

import json
from dataclasses import dataclass
from typing import Any

import pytest

from application.common.export.config.export_config import ExportConfig
from application.common.export.exporters.data_exporter import DataExporter
from application.common.export.formats.export_format import ExportFormat


@dataclass
class SampleRecord:
    """Sample record for testing."""

    id: str
    name: str
    email: str
    age: int


class SampleSerializer:
    """Sample serializer for testing."""

    def to_dict(self, obj: SampleRecord) -> dict[str, Any]:
        return {"id": obj.id, "name": obj.name, "email": obj.email, "age": obj.age}

    def from_dict(self, data: dict[str, Any]) -> SampleRecord:
        return SampleRecord(id=data["id"], name=data["name"], email=data["email"], age=int(data["age"]))


class TestDataExporterJSON:
    """Tests for JSON export."""

    def test_export_json_with_metadata(self) -> None:
        """Test JSON export with metadata."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [
            SampleRecord(id="1", name="Alice", email="alice@test.com", age=30),
            SampleRecord(id="2", name="Bob", email="bob@test.com", age=25),
        ]
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=True)

        content, result = exporter.export_json(records, config)

        assert result.format == ExportFormat.JSON
        assert result.record_count == 2
        assert result.file_size_bytes > 0
        assert result.checksum != ""

        data = json.loads(content.decode())
        assert "metadata" in data
        assert "data" in data
        assert data["metadata"]["record_count"] == 2
        assert len(data["data"]) == 2

    def test_export_json_without_metadata(self) -> None:
        """Test JSON export without metadata."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)

        content, _result = exporter.export_json(records, config)

        data = json.loads(content.decode())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Alice"

    def test_export_json_empty_records(self) -> None:
        """Test JSON export with empty records."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=True)

        content, result = exporter.export_json([], config)

        assert result.record_count == 0
        data = json.loads(content.decode())
        assert data["metadata"]["record_count"] == 0
        assert data["data"] == []

    def test_export_json_include_fields(self) -> None:
        """Test JSON export with field filtering (include)."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(
            format=ExportFormat.JSON,
            include_fields=["id", "name"],
            include_metadata=False,
        )

        content, _result = exporter.export_json(records, config)

        data = json.loads(content.decode())
        assert "id" in data[0]
        assert "name" in data[0]
        assert "email" not in data[0]
        assert "age" not in data[0]

    def test_export_json_exclude_fields(self) -> None:
        """Test JSON export with field filtering (exclude)."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(
            format=ExportFormat.JSON,
            exclude_fields=["email", "age"],
            include_metadata=False,
        )

        content, _result = exporter.export_json(records, config)

        data = json.loads(content.decode())
        assert "id" in data[0]
        assert "name" in data[0]
        assert "email" not in data[0]
        assert "age" not in data[0]


class TestDataExporterCSV:
    """Tests for CSV export."""

    def test_export_csv_basic(self) -> None:
        """Test basic CSV export."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [
            SampleRecord(id="1", name="Alice", email="alice@test.com", age=30),
            SampleRecord(id="2", name="Bob", email="bob@test.com", age=25),
        ]
        config = ExportConfig(format=ExportFormat.CSV)

        content, result = exporter.export_csv(records, config)

        assert result.format == ExportFormat.CSV
        assert result.record_count == 2
        assert result.file_size_bytes > 0

        lines = content.decode().strip().split("\n")
        assert len(lines) == 3  # header + 2 records
        assert "id" in lines[0]
        assert "name" in lines[0]

    def test_export_csv_empty_records(self) -> None:
        """Test CSV export with empty records."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        config = ExportConfig(format=ExportFormat.CSV)

        content, result = exporter.export_csv([], config)

        assert result.record_count == 0
        assert result.file_size_bytes == 0
        assert content == b""

    def test_export_csv_with_field_filter(self) -> None:
        """Test CSV export with field filtering."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.CSV, include_fields=["id", "name"])

        content, _result = exporter.export_csv(records, config)

        lines = content.decode().strip().split("\n")
        header = lines[0]
        assert "id" in header
        assert "name" in header
        assert "email" not in header


class TestDataExporterJSONL:
    """Tests for JSONL export."""

    def test_export_jsonl_basic(self) -> None:
        """Test basic JSONL export."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [
            SampleRecord(id="1", name="Alice", email="alice@test.com", age=30),
            SampleRecord(id="2", name="Bob", email="bob@test.com", age=25),
        ]
        config = ExportConfig(format=ExportFormat.JSONL)

        content, result = exporter.export_jsonl(records, config)

        assert result.format == ExportFormat.JSONL
        assert result.record_count == 2

        lines = content.decode().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert "name" in data

    def test_export_jsonl_empty_records(self) -> None:
        """Test JSONL export with empty records."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        config = ExportConfig(format=ExportFormat.JSONL)

        content, result = exporter.export_jsonl([], config)

        assert result.record_count == 0
        assert content == b""

    def test_export_jsonl_with_field_filter(self) -> None:
        """Test JSONL export with field filtering."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.JSONL, exclude_fields=["email", "age"])

        content, _result = exporter.export_jsonl(records, config)

        data = json.loads(content.decode())
        assert "id" in data
        assert "name" in data
        assert "email" not in data


class TestDataExporterGeneric:
    """Tests for generic export method."""

    def test_export_dispatches_to_json(self) -> None:
        """Test export method dispatches to JSON."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)

        _content, result = exporter.export(records, config)

        assert result.format == ExportFormat.JSON

    def test_export_dispatches_to_csv(self) -> None:
        """Test export method dispatches to CSV."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.CSV)

        _content, result = exporter.export(records, config)

        assert result.format == ExportFormat.CSV

    def test_export_dispatches_to_jsonl(self) -> None:
        """Test export method dispatches to JSONL."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.JSONL)

        _content, result = exporter.export(records, config)

        assert result.format == ExportFormat.JSONL

    def test_export_unsupported_format(self) -> None:
        """Test export with unsupported format raises error."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.PARQUET)

        with pytest.raises(ValueError, match="Unsupported format"):
            exporter.export(records, config)


class TestDataExporterChecksum:
    """Tests for checksum computation."""

    def test_checksum_is_consistent(self) -> None:
        """Test checksum is consistent for same data."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)

        _, result1 = exporter.export_json(records, config)
        _, result2 = exporter.export_json(records, config)

        assert result1.checksum == result2.checksum

    def test_checksum_differs_for_different_data(self) -> None:
        """Test checksum differs for different data."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records1 = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        records2 = [SampleRecord(id="2", name="Bob", email="bob@test.com", age=25)]
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)

        _, result1 = exporter.export_json(records1, config)
        _, result2 = exporter.export_json(records2, config)

        assert result1.checksum != result2.checksum

    def test_checksum_length(self) -> None:
        """Test checksum is truncated to 16 chars."""
        serializer = SampleSerializer()
        exporter = DataExporter(serializer)
        records = [SampleRecord(id="1", name="Alice", email="alice@test.com", age=30)]
        config = ExportConfig(format=ExportFormat.JSON)

        _, result = exporter.export_json(records, config)

        assert len(result.checksum) == 16
