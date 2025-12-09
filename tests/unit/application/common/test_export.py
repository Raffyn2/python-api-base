"""Unit tests for export module.

Tests for data_exporter.py, data_importer.py, export_config.py,
export_format.py, export_result.py, import_result.py.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 6.1, 6.2, 6.3**
"""

import json
from dataclasses import dataclass
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from application.common.export.config.export_config import ExportConfig
from application.common.export.exporters.data_exporter import DataExporter
from application.common.export.formats.export_format import ExportFormat
from application.common.export.importers.data_importer import DataImporter
from application.common.export.results.export_result import ExportResult
from application.common.export.results.import_result import ImportResult
from application.common.export.serializers.data_serializer import DataSerializer


# Test data model
@dataclass
class TestRecord:
    """Test record for export/import tests."""

    id: str
    name: str
    value: int


class TestRecordSerializer:
    """Serializer for TestRecord."""

    def to_dict(self, obj: TestRecord) -> dict[str, Any]:
        return {"id": obj.id, "name": obj.name, "value": obj.value}

    def from_dict(self, data: dict[str, Any]) -> TestRecord:
        return TestRecord(
            id=str(data["id"]),
            name=str(data["name"]),
            value=int(data["value"]),
        )


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_json_format_value(self) -> None:
        """Test JSON format has correct value."""
        assert ExportFormat.JSON.value == "json"

    def test_csv_format_value(self) -> None:
        """Test CSV format has correct value."""
        assert ExportFormat.CSV.value == "csv"

    def test_jsonl_format_value(self) -> None:
        """Test JSONL format has correct value."""
        assert ExportFormat.JSONL.value == "jsonl"

    def test_parquet_format_value(self) -> None:
        """Test Parquet format has correct value."""
        assert ExportFormat.PARQUET.value == "parquet"

    def test_all_formats_exist(self) -> None:
        """Test all expected formats exist."""
        formats = [f.value for f in ExportFormat]
        assert "json" in formats
        assert "csv" in formats
        assert "jsonl" in formats
        assert "parquet" in formats


class TestExportConfig:
    """Tests for ExportConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ExportConfig()
        assert config.format == ExportFormat.JSON
        assert config.include_fields is None
        assert config.exclude_fields is None
        assert config.batch_size == 1000
        assert config.compress is False
        assert config.include_metadata is True

    def test_custom_format(self) -> None:
        """Test custom format configuration."""
        config = ExportConfig(format=ExportFormat.CSV)
        assert config.format == ExportFormat.CSV

    def test_include_fields(self) -> None:
        """Test include_fields configuration."""
        config = ExportConfig(include_fields=["id", "name"])
        assert config.include_fields == ["id", "name"]

    def test_exclude_fields(self) -> None:
        """Test exclude_fields configuration."""
        config = ExportConfig(exclude_fields=["value"])
        assert config.exclude_fields == ["value"]

    def test_batch_size(self) -> None:
        """Test batch_size configuration."""
        config = ExportConfig(batch_size=500)
        assert config.batch_size == 500

    def test_compress_flag(self) -> None:
        """Test compress flag configuration."""
        config = ExportConfig(compress=True)
        assert config.compress is True

    def test_metadata_flag(self) -> None:
        """Test include_metadata flag configuration."""
        config = ExportConfig(include_metadata=False)
        assert config.include_metadata is False


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_creation(self) -> None:
        """Test ExportResult creation."""
        result = ExportResult(
            format=ExportFormat.JSON,
            record_count=10,
            file_size_bytes=1024,
            duration_ms=50.5,
            checksum="abc123",
        )
        assert result.format == ExportFormat.JSON
        assert result.record_count == 10
        assert result.file_size_bytes == 1024
        assert result.duration_ms == 50.5
        assert result.checksum == "abc123"
        assert result.metadata == {}

    def test_with_metadata(self) -> None:
        """Test ExportResult with metadata."""
        result = ExportResult(
            format=ExportFormat.CSV,
            record_count=5,
            file_size_bytes=512,
            duration_ms=25.0,
            checksum="def456",
            metadata={"source": "test"},
        )
        assert result.metadata == {"source": "test"}


class TestImportResult:
    """Tests for ImportResult dataclass."""

    def test_creation(self) -> None:
        """Test ImportResult creation."""
        result = ImportResult(
            records_processed=100,
            records_imported=95,
            records_skipped=3,
            records_failed=2,
        )
        assert result.records_processed == 100
        assert result.records_imported == 95
        assert result.records_skipped == 3
        assert result.records_failed == 2
        assert result.errors == []
        assert result.duration_ms == 0.0

    def test_with_errors(self) -> None:
        """Test ImportResult with errors."""
        result = ImportResult(
            records_processed=10,
            records_imported=8,
            records_skipped=0,
            records_failed=2,
            errors=["Error 1", "Error 2"],
            duration_ms=100.0,
        )
        assert len(result.errors) == 2
        assert result.duration_ms == 100.0


class TestDataExporter:
    """Tests for DataExporter class."""

    @pytest.fixture
    def exporter(self) -> DataExporter[TestRecord]:
        """Create exporter with test serializer."""
        return DataExporter(TestRecordSerializer())

    @pytest.fixture
    def sample_records(self) -> list[TestRecord]:
        """Create sample test records."""
        return [
            TestRecord(id="1", name="Item 1", value=100),
            TestRecord(id="2", name="Item 2", value=200),
            TestRecord(id="3", name="Item 3", value=300),
        ]

    def test_export_json_with_metadata(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test JSON export with metadata."""
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=True)
        content, result = exporter.export_json(sample_records, config)

        assert result.format == ExportFormat.JSON
        assert result.record_count == 3
        assert result.file_size_bytes > 0
        assert result.checksum != ""

        data = json.loads(content.decode())
        assert "metadata" in data
        assert "data" in data
        assert len(data["data"]) == 3

    def test_export_json_without_metadata(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test JSON export without metadata."""
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)
        content, result = exporter.export_json(sample_records, config)

        data = json.loads(content.decode())
        assert isinstance(data, list)
        assert len(data) == 3

    def test_export_json_with_include_fields(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test JSON export with field filtering (include)."""
        config = ExportConfig(
            format=ExportFormat.JSON,
            include_fields=["id", "name"],
            include_metadata=False,
        )
        content, result = exporter.export_json(sample_records, config)

        data = json.loads(content.decode())
        for item in data:
            assert "id" in item
            assert "name" in item
            assert "value" not in item

    def test_export_json_with_exclude_fields(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test JSON export with field filtering (exclude)."""
        config = ExportConfig(
            format=ExportFormat.JSON,
            exclude_fields=["value"],
            include_metadata=False,
        )
        content, result = exporter.export_json(sample_records, config)

        data = json.loads(content.decode())
        for item in data:
            assert "id" in item
            assert "name" in item
            assert "value" not in item

    def test_export_csv(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test CSV export."""
        config = ExportConfig(format=ExportFormat.CSV)
        content, result = exporter.export_csv(sample_records, config)

        assert result.format == ExportFormat.CSV
        assert result.record_count == 3
        assert result.file_size_bytes > 0

        lines = content.decode().strip().split("\n")
        assert len(lines) == 4  # header + 3 records

    def test_export_csv_empty(self, exporter: DataExporter[TestRecord]) -> None:
        """Test CSV export with empty records."""
        config = ExportConfig(format=ExportFormat.CSV)
        content, result = exporter.export_csv([], config)

        assert result.record_count == 0
        assert result.file_size_bytes == 0
        assert content == b""

    def test_export_jsonl(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test JSONL export."""
        config = ExportConfig(format=ExportFormat.JSONL)
        content, result = exporter.export_jsonl(sample_records, config)

        assert result.format == ExportFormat.JSONL
        assert result.record_count == 3

        lines = content.decode().strip().split("\n")
        assert len(lines) == 3
        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert "name" in data
            assert "value" in data

    def test_export_generic_json(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test generic export method with JSON format."""
        config = ExportConfig(format=ExportFormat.JSON)
        content, result = exporter.export(sample_records, config)
        assert result.format == ExportFormat.JSON

    def test_export_generic_csv(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test generic export method with CSV format."""
        config = ExportConfig(format=ExportFormat.CSV)
        content, result = exporter.export(sample_records, config)
        assert result.format == ExportFormat.CSV

    def test_export_generic_jsonl(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test generic export method with JSONL format."""
        config = ExportConfig(format=ExportFormat.JSONL)
        content, result = exporter.export(sample_records, config)
        assert result.format == ExportFormat.JSONL

    def test_export_unsupported_format(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test export with unsupported format raises error."""
        config = ExportConfig(format=ExportFormat.PARQUET)
        with pytest.raises(ValueError, match="Unsupported format"):
            exporter.export(sample_records, config)

    def test_checksum_consistency(
        self, exporter: DataExporter[TestRecord], sample_records: list[TestRecord]
    ) -> None:
        """Test that same data produces same checksum."""
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)
        _, result1 = exporter.export_json(sample_records, config)
        _, result2 = exporter.export_json(sample_records, config)
        assert result1.checksum == result2.checksum


class TestDataImporter:
    """Tests for DataImporter class."""

    @pytest.fixture
    def importer(self) -> DataImporter[TestRecord]:
        """Create importer with test serializer."""
        return DataImporter(TestRecordSerializer())

    @pytest.fixture
    def exporter(self) -> DataExporter[TestRecord]:
        """Create exporter for round-trip tests."""
        return DataExporter(TestRecordSerializer())

    def test_import_json(self, importer: DataImporter[TestRecord]) -> None:
        """Test JSON import."""
        content = b'[{"id": "1", "name": "Test", "value": 100}]'
        records, result = importer.import_json(content)

        assert len(records) == 1
        assert records[0].id == "1"
        assert records[0].name == "Test"
        assert records[0].value == 100
        assert result.records_imported == 1
        assert result.records_failed == 0

    def test_import_json_with_metadata(
        self, importer: DataImporter[TestRecord]
    ) -> None:
        """Test JSON import with metadata wrapper."""
        content = b'{"metadata": {}, "data": [{"id": "1", "name": "Test", "value": 100}]}'
        records, result = importer.import_json(content)

        assert len(records) == 1
        assert result.records_imported == 1

    def test_import_json_invalid(self, importer: DataImporter[TestRecord]) -> None:
        """Test JSON import with invalid JSON."""
        content = b"not valid json"
        records, result = importer.import_json(content)

        assert len(records) == 0
        assert len(result.errors) > 0

    def test_import_json_invalid_record(
        self, importer: DataImporter[TestRecord]
    ) -> None:
        """Test JSON import with invalid record data."""
        content = b'[{"id": "1", "name": "Test", "value": "not_a_number"}]'
        records, result = importer.import_json(content)

        assert result.records_failed == 1
        assert len(result.errors) > 0

    def test_import_csv(self, importer: DataImporter[TestRecord]) -> None:
        """Test CSV import."""
        content = b"id,name,value\n1,Test,100\n2,Test2,200"
        records, result = importer.import_csv(content)

        assert len(records) == 2
        assert result.records_imported == 2
        assert result.records_failed == 0

    def test_import_csv_invalid(self, importer: DataImporter[TestRecord]) -> None:
        """Test CSV import with invalid data."""
        content = b"id,name,value\n1,Test,not_a_number"
        records, result = importer.import_csv(content)

        assert result.records_failed == 1

    def test_import_jsonl(self, importer: DataImporter[TestRecord]) -> None:
        """Test JSONL import."""
        content = b'{"id": "1", "name": "Test1", "value": 100}\n{"id": "2", "name": "Test2", "value": 200}'
        records, result = importer.import_jsonl(content)

        assert len(records) == 2
        assert result.records_imported == 2

    def test_import_jsonl_with_empty_lines(
        self, importer: DataImporter[TestRecord]
    ) -> None:
        """Test JSONL import ignores empty lines."""
        content = b'{"id": "1", "name": "Test", "value": 100}\n\n'
        records, result = importer.import_jsonl(content)

        assert len(records) == 1

    def test_import_jsonl_invalid_line(
        self, importer: DataImporter[TestRecord]
    ) -> None:
        """Test JSONL import with invalid line."""
        content = b'{"id": "1", "name": "Test", "value": 100}\nnot json'
        records, result = importer.import_jsonl(content)

        assert result.records_imported == 1
        assert result.records_failed == 1

    def test_import_data_json(self, importer: DataImporter[TestRecord]) -> None:
        """Test generic import with JSON format."""
        content = b'[{"id": "1", "name": "Test", "value": 100}]'
        records, result = importer.import_data(content, ExportFormat.JSON)
        assert len(records) == 1

    def test_import_data_csv(self, importer: DataImporter[TestRecord]) -> None:
        """Test generic import with CSV format."""
        content = b"id,name,value\n1,Test,100"
        records, result = importer.import_data(content, ExportFormat.CSV)
        assert len(records) == 1

    def test_import_data_jsonl(self, importer: DataImporter[TestRecord]) -> None:
        """Test generic import with JSONL format."""
        content = b'{"id": "1", "name": "Test", "value": 100}'
        records, result = importer.import_data(content, ExportFormat.JSONL)
        assert len(records) == 1

    def test_import_data_unsupported(
        self, importer: DataImporter[TestRecord]
    ) -> None:
        """Test import with unsupported format raises error."""
        with pytest.raises(ValueError, match="Unsupported format"):
            importer.import_data(b"", ExportFormat.PARQUET)


class TestExportImportRoundTrip:
    """Round-trip tests for export/import.

    **Feature: test-coverage-80-percent-v3, Property 12: Export/Import Round-trip**
    **Validates: Requirements 6.1, 6.2, 6.3**
    """

    @pytest.fixture
    def exporter(self) -> DataExporter[TestRecord]:
        return DataExporter(TestRecordSerializer())

    @pytest.fixture
    def importer(self) -> DataImporter[TestRecord]:
        return DataImporter(TestRecordSerializer())

    def test_json_roundtrip(
        self,
        exporter: DataExporter[TestRecord],
        importer: DataImporter[TestRecord],
    ) -> None:
        """Test JSON export/import round-trip."""
        original = [
            TestRecord(id="1", name="Test1", value=100),
            TestRecord(id="2", name="Test2", value=200),
        ]
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)

        content, _ = exporter.export_json(original, config)
        imported, result = importer.import_json(content)

        assert len(imported) == len(original)
        for orig, imp in zip(original, imported):
            assert orig.id == imp.id
            assert orig.name == imp.name
            assert orig.value == imp.value

    def test_csv_roundtrip(
        self,
        exporter: DataExporter[TestRecord],
        importer: DataImporter[TestRecord],
    ) -> None:
        """Test CSV export/import round-trip."""
        original = [
            TestRecord(id="1", name="Test1", value=100),
            TestRecord(id="2", name="Test2", value=200),
        ]
        config = ExportConfig(format=ExportFormat.CSV)

        content, _ = exporter.export_csv(original, config)
        imported, result = importer.import_csv(content)

        assert len(imported) == len(original)
        for orig, imp in zip(original, imported):
            assert orig.id == imp.id
            assert orig.name == imp.name
            assert orig.value == imp.value

    def test_jsonl_roundtrip(
        self,
        exporter: DataExporter[TestRecord],
        importer: DataImporter[TestRecord],
    ) -> None:
        """Test JSONL export/import round-trip."""
        original = [
            TestRecord(id="1", name="Test1", value=100),
            TestRecord(id="2", name="Test2", value=200),
        ]
        config = ExportConfig(format=ExportFormat.JSONL)

        content, _ = exporter.export_jsonl(original, config)
        imported, result = importer.import_jsonl(content)

        assert len(imported) == len(original)
        for orig, imp in zip(original, imported):
            assert orig.id == imp.id
            assert orig.name == imp.name
            assert orig.value == imp.value

    @given(
        records=st.lists(
            st.builds(
                TestRecord,
                id=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
                name=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
                value=st.integers(min_value=0, max_value=1000000),
            ),
            min_size=0,
            max_size=20,
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_json_roundtrip_property(self, records: list[TestRecord]) -> None:
        """Property test: JSON export/import preserves data.

        **Feature: test-coverage-80-percent-v3, Property 12: Export/Import Round-trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        exporter = DataExporter(TestRecordSerializer())
        importer = DataImporter(TestRecordSerializer())
        config = ExportConfig(format=ExportFormat.JSON, include_metadata=False)

        content, _ = exporter.export_json(records, config)
        imported, result = importer.import_json(content)

        assert len(imported) == len(records)
        for orig, imp in zip(records, imported):
            assert orig.id == imp.id
            assert orig.name == imp.name
            assert orig.value == imp.value

    @given(
        records=st.lists(
            st.builds(
                TestRecord,
                id=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
                name=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz"),
                value=st.integers(min_value=0, max_value=1000000),
            ),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_csv_roundtrip_property(self, records: list[TestRecord]) -> None:
        """Property test: CSV export/import preserves data.

        **Feature: test-coverage-80-percent-v3, Property 12: Export/Import Round-trip**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        exporter = DataExporter(TestRecordSerializer())
        importer = DataImporter(TestRecordSerializer())
        config = ExportConfig(format=ExportFormat.CSV)

        content, _ = exporter.export_csv(records, config)
        imported, result = importer.import_csv(content)

        assert len(imported) == len(records)
        for orig, imp in zip(records, imported):
            assert orig.id == imp.id
            assert orig.name == imp.name
            assert orig.value == imp.value
