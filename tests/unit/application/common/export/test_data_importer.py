"""Unit tests for DataImporter.

Tests JSON, CSV, and JSONL import functionality.
"""

import json
from dataclasses import dataclass
from typing import Any

import pytest

from application.common.export.formats.export_format import ExportFormat
from application.common.export.importers.data_importer import DataImporter


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


class FailingSerializer:
    """Serializer that fails on specific records."""

    def to_dict(self, obj: SampleRecord) -> dict[str, Any]:
        return {"id": obj.id, "name": obj.name, "email": obj.email, "age": obj.age}

    def from_dict(self, data: dict[str, Any]) -> SampleRecord:
        if data.get("id") == "fail":
            raise ValueError("Invalid record")
        return SampleRecord(id=data["id"], name=data["name"], email=data["email"], age=int(data["age"]))


class TestDataImporterJSON:
    """Tests for JSON import."""

    def test_import_json_basic(self) -> None:
        """Test basic JSON import."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        data = [
            {"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30},
            {"id": "2", "name": "Bob", "email": "bob@test.com", "age": 25},
        ]
        content = json.dumps(data).encode()

        records, result = importer.import_json(content)

        assert len(records) == 2
        assert result.records_processed == 2
        assert result.records_imported == 2
        assert result.records_failed == 0
        assert records[0].name == "Alice"
        assert records[1].name == "Bob"

    def test_import_json_with_metadata_wrapper(self) -> None:
        """Test JSON import with metadata wrapper."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        data = {
            "metadata": {"exported_at": "2024-01-01", "record_count": 1},
            "data": [{"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}],
        }
        content = json.dumps(data).encode()

        records, result = importer.import_json(content)

        assert len(records) == 1
        assert result.records_imported == 1
        assert records[0].name == "Alice"

    def test_import_json_empty(self) -> None:
        """Test JSON import with empty array."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = json.dumps([]).encode()

        records, result = importer.import_json(content)

        assert len(records) == 0
        assert result.records_processed == 0
        assert result.records_imported == 0

    def test_import_json_with_failures(self) -> None:
        """Test JSON import with some failures."""
        serializer = FailingSerializer()
        importer = DataImporter(serializer)
        data = [
            {"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30},
            {"id": "fail", "name": "Bad", "email": "bad@test.com", "age": 0},
            {"id": "2", "name": "Bob", "email": "bob@test.com", "age": 25},
        ]
        content = json.dumps(data).encode()

        records, result = importer.import_json(content)

        assert len(records) == 2
        assert result.records_processed == 3
        assert result.records_imported == 2
        assert result.records_failed == 1
        assert len(result.errors) == 1

    def test_import_json_invalid_format(self) -> None:
        """Test JSON import with invalid JSON."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = b"not valid json"

        records, result = importer.import_json(content)

        assert len(records) == 0
        assert len(result.errors) == 1
        assert "Parse error" in result.errors[0]


class TestDataImporterCSV:
    """Tests for CSV import."""

    def test_import_csv_basic(self) -> None:
        """Test basic CSV import."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = b"id,name,email,age\n1,Alice,alice@test.com,30\n2,Bob,bob@test.com,25"

        records, result = importer.import_csv(content)

        assert len(records) == 2
        assert result.records_processed == 2
        assert result.records_imported == 2
        assert records[0].name == "Alice"
        assert records[1].name == "Bob"

    def test_import_csv_empty(self) -> None:
        """Test CSV import with only header."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = b"id,name,email,age\n"

        records, result = importer.import_csv(content)

        assert len(records) == 0
        assert result.records_processed == 0

    def test_import_csv_with_failures(self) -> None:
        """Test CSV import with some failures."""
        serializer = FailingSerializer()
        importer = DataImporter(serializer)
        content = b"id,name,email,age\n1,Alice,alice@test.com,30\nfail,Bad,bad@test.com,0"

        records, result = importer.import_csv(content)

        assert len(records) == 1
        assert result.records_processed == 2
        assert result.records_imported == 1
        assert result.records_failed == 1

    def test_import_csv_invalid_format(self) -> None:
        """Test CSV import with invalid format."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        # Binary content that can't be decoded
        content = bytes([0x80, 0x81, 0x82])

        records, result = importer.import_csv(content)

        assert len(records) == 0
        assert len(result.errors) == 1
        assert "Parse error" in result.errors[0]


class TestDataImporterJSONL:
    """Tests for JSONL import."""

    def test_import_jsonl_basic(self) -> None:
        """Test basic JSONL import."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        lines = [
            json.dumps({"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}),
            json.dumps({"id": "2", "name": "Bob", "email": "bob@test.com", "age": 25}),
        ]
        content = "\n".join(lines).encode()

        records, result = importer.import_jsonl(content)

        assert len(records) == 2
        assert result.records_processed == 2
        assert result.records_imported == 2
        assert records[0].name == "Alice"

    def test_import_jsonl_empty(self) -> None:
        """Test JSONL import with empty content."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = b""

        records, result = importer.import_jsonl(content)

        assert len(records) == 0
        assert result.records_processed == 0

    def test_import_jsonl_with_empty_lines(self) -> None:
        """Test JSONL import skips empty lines."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        lines = [
            json.dumps({"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}),
            "",
            json.dumps({"id": "2", "name": "Bob", "email": "bob@test.com", "age": 25}),
        ]
        content = "\n".join(lines).encode()

        records, result = importer.import_jsonl(content)

        assert len(records) == 2
        assert result.records_processed == 2

    def test_import_jsonl_with_failures(self) -> None:
        """Test JSONL import with some failures."""
        serializer = FailingSerializer()
        importer = DataImporter(serializer)
        lines = [
            json.dumps({"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}),
            json.dumps({"id": "fail", "name": "Bad", "email": "bad@test.com", "age": 0}),
        ]
        content = "\n".join(lines).encode()

        records, result = importer.import_jsonl(content)

        assert len(records) == 1
        assert result.records_failed == 1

    def test_import_jsonl_invalid_line(self) -> None:
        """Test JSONL import with invalid JSON line."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        lines = [
            json.dumps({"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}),
            "not valid json",
        ]
        content = "\n".join(lines).encode()

        records, result = importer.import_jsonl(content)

        assert len(records) == 1
        assert result.records_failed == 1


class TestDataImporterGeneric:
    """Tests for generic import method."""

    def test_import_data_dispatches_to_json(self) -> None:
        """Test import_data dispatches to JSON."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        data = [{"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}]
        content = json.dumps(data).encode()

        records, _result = importer.import_data(content, ExportFormat.JSON)

        assert len(records) == 1
        assert records[0].name == "Alice"

    def test_import_data_dispatches_to_csv(self) -> None:
        """Test import_data dispatches to CSV."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = b"id,name,email,age\n1,Alice,alice@test.com,30"

        records, _result = importer.import_data(content, ExportFormat.CSV)

        assert len(records) == 1
        assert records[0].name == "Alice"

    def test_import_data_dispatches_to_jsonl(self) -> None:
        """Test import_data dispatches to JSONL."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = json.dumps({"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}).encode()

        records, _result = importer.import_data(content, ExportFormat.JSONL)

        assert len(records) == 1
        assert records[0].name == "Alice"

    def test_import_data_unsupported_format(self) -> None:
        """Test import_data with unsupported format raises error."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        content = b"some content"

        with pytest.raises(ValueError, match="Unsupported format"):
            importer.import_data(content, ExportFormat.PARQUET)


class TestDataImporterDuration:
    """Tests for duration tracking."""

    def test_import_tracks_duration(self) -> None:
        """Test import tracks duration."""
        serializer = SampleSerializer()
        importer = DataImporter(serializer)
        data = [{"id": "1", "name": "Alice", "email": "alice@test.com", "age": 30}]
        content = json.dumps(data).encode()

        _, result = importer.import_json(content)

        assert result.duration_ms >= 0
