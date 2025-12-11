"""Unit tests for audit filters and exporters.

Tests AuditQueryFilters, JsonAuditExporter, CsvAuditExporter.
"""

import pytest
from pydantic import BaseModel

from infrastructure.audit import (
    AuditAction,
    AuditRecord,
    CsvAuditExporter,
    CsvExportConfig,
    ExportFormat,
    JsonAuditExporter,
    JsonExportConfig,
)


class SampleEntity(BaseModel):
    """Sample entity for testing."""

    id: str
    name: str


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_json_value(self) -> None:
        """Test JSON format value."""
        assert ExportFormat.JSON.value == "json"

    def test_csv_value(self) -> None:
        """Test CSV format value."""
        assert ExportFormat.CSV.value == "csv"

    def test_xml_value(self) -> None:
        """Test XML format value."""
        assert ExportFormat.XML.value == "xml"


class TestJsonExportConfig:
    """Tests for JsonExportConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = JsonExportConfig()
        assert config.pretty is True
        assert config.include_metadata is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = JsonExportConfig(pretty=False, include_metadata=False)
        assert config.pretty is False
        assert config.include_metadata is False


class TestJsonAuditExporter:
    """Tests for JsonAuditExporter."""

    @pytest.fixture()
    def exporter(self) -> JsonAuditExporter:
        """Create test exporter."""
        return JsonAuditExporter()

    @pytest.fixture()
    def sample_records(self) -> list[AuditRecord[SampleEntity]]:
        """Create sample audit records."""
        return [
            AuditRecord(
                entity_type="User",
                entity_id="user-1",
                action=AuditAction.CREATE,
                user_id="admin-1",
                metadata={"source": "api"},
            ),
            AuditRecord(
                entity_type="User",
                entity_id="user-2",
                action=AuditAction.UPDATE,
                user_id="admin-1",
            ),
        ]

    def test_export_default_config(
        self,
        exporter: JsonAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export with default config."""
        result = exporter.export(sample_records)
        assert isinstance(result, bytes)
        decoded = result.decode("utf-8")
        assert "User" in decoded
        assert "user-1" in decoded
        assert "CREATE" in decoded

    def test_export_pretty_format(
        self,
        exporter: JsonAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export with pretty formatting."""
        config = JsonExportConfig(pretty=True)
        result = exporter.export(sample_records, config)
        decoded = result.decode("utf-8")
        assert "\n" in decoded  # Pretty format has newlines

    def test_export_compact_format(
        self,
        exporter: JsonAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export with compact formatting."""
        config = JsonExportConfig(pretty=False)
        result = exporter.export(sample_records, config)
        decoded = result.decode("utf-8")
        # Compact format has no indentation newlines
        assert decoded.count("\n") == 0

    def test_export_without_metadata(
        self,
        exporter: JsonAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export excluding metadata."""
        config = JsonExportConfig(include_metadata=False)
        result = exporter.export(sample_records, config)
        decoded = result.decode("utf-8")
        # Metadata should be excluded
        assert '"metadata":' not in decoded or '"metadata": {}' in decoded

    def test_export_empty_records(self, exporter: JsonAuditExporter) -> None:
        """Test export with empty records."""
        result = exporter.export([])
        assert result == b"[]"


class TestCsvExportConfig:
    """Tests for CsvExportConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CsvExportConfig()
        assert config.delimiter == ","
        assert config.include_header is True

    def test_custom_delimiter(self) -> None:
        """Test custom delimiter."""
        config = CsvExportConfig(delimiter=";")
        assert config.delimiter == ";"


class TestCsvAuditExporter:
    """Tests for CsvAuditExporter."""

    @pytest.fixture()
    def exporter(self) -> CsvAuditExporter:
        """Create test exporter."""
        return CsvAuditExporter()

    @pytest.fixture()
    def sample_records(self) -> list[AuditRecord[SampleEntity]]:
        """Create sample audit records."""
        return [
            AuditRecord(
                entity_type="User",
                entity_id="user-1",
                action=AuditAction.CREATE,
                user_id="admin-1",
            ),
            AuditRecord(
                entity_type="User",
                entity_id="user-2",
                action=AuditAction.UPDATE,
                user_id="admin-2",
            ),
        ]

    def test_export_with_header(
        self,
        exporter: CsvAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export with header row."""
        config = CsvExportConfig(include_header=True)
        result = exporter.export(sample_records, config)
        decoded = result.decode("utf-8")
        lines = decoded.split("\n")
        assert len(lines) == 3  # Header + 2 records
        assert "entity_type" in lines[0]

    def test_export_without_header(
        self,
        exporter: CsvAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export without header row."""
        config = CsvExportConfig(include_header=False)
        result = exporter.export(sample_records, config)
        decoded = result.decode("utf-8")
        lines = decoded.split("\n")
        assert len(lines) == 2  # Just 2 records

    def test_export_custom_delimiter(
        self,
        exporter: CsvAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export with custom delimiter."""
        config = CsvExportConfig(delimiter=";")
        result = exporter.export(sample_records, config)
        decoded = result.decode("utf-8")
        assert ";" in decoded

    def test_export_empty_records(self, exporter: CsvAuditExporter) -> None:
        """Test export with empty records."""
        result = exporter.export([])
        assert result == b""

    def test_export_default_config(
        self,
        exporter: CsvAuditExporter,
        sample_records: list[AuditRecord[SampleEntity]],
    ) -> None:
        """Test export with default config."""
        result = exporter.export(sample_records)
        assert isinstance(result, bytes)
        decoded = result.decode("utf-8")
        assert "User" in decoded
        assert "user-1" in decoded
