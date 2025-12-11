"""Unit tests for export types and configuration.

Tests ExportFormat, ExportConfig, ExportResult, and ImportResult.
"""

from application.common.export import (
    ExportConfig,
    ExportFormat,
    ExportResult,
    ImportResult,
)


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_json_format(self) -> None:
        """Test JSON format value."""
        assert ExportFormat.JSON.value == "json"

    def test_csv_format(self) -> None:
        """Test CSV format value."""
        assert ExportFormat.CSV.value == "csv"

    def test_jsonl_format(self) -> None:
        """Test JSONL format value."""
        assert ExportFormat.JSONL.value == "jsonl"

    def test_parquet_format(self) -> None:
        """Test Parquet format value."""
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

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ExportConfig(
            format=ExportFormat.CSV,
            include_fields=["id", "name", "email"],
            exclude_fields=["password"],
            batch_size=500,
            compress=True,
            include_metadata=False,
        )
        assert config.format == ExportFormat.CSV
        assert config.include_fields == ["id", "name", "email"]
        assert config.exclude_fields == ["password"]
        assert config.batch_size == 500
        assert config.compress is True
        assert config.include_metadata is False

    def test_parquet_format_config(self) -> None:
        """Test configuration with Parquet format."""
        config = ExportConfig(format=ExportFormat.PARQUET, compress=True)
        assert config.format == ExportFormat.PARQUET

    def test_jsonl_format_config(self) -> None:
        """Test configuration with JSONL format."""
        config = ExportConfig(format=ExportFormat.JSONL)
        assert config.format == ExportFormat.JSONL


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_export_result_creation(self) -> None:
        """Test export result creation."""
        result = ExportResult(
            format=ExportFormat.JSON,
            record_count=1000,
            file_size_bytes=50000,
            duration_ms=1500.5,
            checksum="abc123def456",
        )
        assert result.format == ExportFormat.JSON
        assert result.record_count == 1000
        assert result.file_size_bytes == 50000
        assert result.duration_ms == 1500.5
        assert result.checksum == "abc123def456"
        assert result.metadata == {}

    def test_export_result_with_metadata(self) -> None:
        """Test export result with metadata."""
        result = ExportResult(
            format=ExportFormat.CSV,
            record_count=500,
            file_size_bytes=25000,
            duration_ms=800.0,
            checksum="xyz789",
            metadata={"exported_by": "system", "version": "1.0"},
        )
        assert result.metadata["exported_by"] == "system"
        assert result.metadata["version"] == "1.0"

    def test_export_result_empty(self) -> None:
        """Test export result with zero records."""
        result = ExportResult(
            format=ExportFormat.JSONL,
            record_count=0,
            file_size_bytes=0,
            duration_ms=10.0,
            checksum="empty",
        )
        assert result.record_count == 0
        assert result.file_size_bytes == 0


class TestImportResult:
    """Tests for ImportResult dataclass."""

    def test_import_result_success(self) -> None:
        """Test successful import result."""
        result = ImportResult(
            records_processed=1000,
            records_imported=1000,
            records_skipped=0,
            records_failed=0,
            duration_ms=2000.0,
        )
        assert result.records_processed == 1000
        assert result.records_imported == 1000
        assert result.records_skipped == 0
        assert result.records_failed == 0
        assert result.errors == []

    def test_import_result_partial(self) -> None:
        """Test partial import result."""
        result = ImportResult(
            records_processed=100,
            records_imported=80,
            records_skipped=10,
            records_failed=10,
            errors=["Row 5: Invalid email", "Row 15: Missing required field"],
            duration_ms=500.0,
        )
        assert result.records_imported == 80
        assert result.records_skipped == 10
        assert result.records_failed == 10
        assert len(result.errors) == 2

    def test_import_result_all_failed(self) -> None:
        """Test import result with all failures."""
        result = ImportResult(
            records_processed=50,
            records_imported=0,
            records_skipped=0,
            records_failed=50,
            errors=["Invalid format"],
        )
        assert result.records_imported == 0
        assert result.records_failed == 50

    def test_import_result_default_values(self) -> None:
        """Test import result default values."""
        result = ImportResult(
            records_processed=10,
            records_imported=10,
            records_skipped=0,
            records_failed=0,
        )
        assert result.errors == []
        assert result.duration_ms == 0.0
