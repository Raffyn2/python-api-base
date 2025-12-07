"""Unit tests for file upload models.

Tests UploadError, FileMetadata, UploadResult, FileValidationConfig.
"""

from datetime import UTC, datetime

import pytest

from application.services.file_upload.models.models import (
    FileMetadata,
    FileValidationConfig,
    UploadError,
    UploadResult,
)


class TestUploadError:
    """Tests for UploadError enum."""

    def test_file_too_large(self) -> None:
        """Test FILE_TOO_LARGE value."""
        assert UploadError.FILE_TOO_LARGE.value == "file_too_large"

    def test_invalid_type(self) -> None:
        """Test INVALID_TYPE value."""
        assert UploadError.INVALID_TYPE.value == "invalid_type"

    def test_invalid_extension(self) -> None:
        """Test INVALID_EXTENSION value."""
        assert UploadError.INVALID_EXTENSION.value == "invalid_extension"

    def test_quota_exceeded(self) -> None:
        """Test QUOTA_EXCEEDED value."""
        assert UploadError.QUOTA_EXCEEDED.value == "quota_exceeded"

    def test_virus_detected(self) -> None:
        """Test VIRUS_DETECTED value."""
        assert UploadError.VIRUS_DETECTED.value == "virus_detected"

    def test_storage_error(self) -> None:
        """Test STORAGE_ERROR value."""
        assert UploadError.STORAGE_ERROR.value == "storage_error"

    def test_checksum_mismatch(self) -> None:
        """Test CHECKSUM_MISMATCH value."""
        assert UploadError.CHECKSUM_MISMATCH.value == "checksum_mismatch"


class TestFileMetadata:
    """Tests for FileMetadata dataclass."""

    def test_creation(self) -> None:
        """Test metadata creation."""
        now = datetime.now(UTC)
        metadata = FileMetadata(
            id="file-123",
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="abc123",
            uploaded_by="user-456",
            uploaded_at=now,
            tenant_id="tenant-789",
        )
        
        assert metadata.id == "file-123"
        assert metadata.filename == "test.pdf"
        assert metadata.content_type == "application/pdf"
        assert metadata.size_bytes == 1024
        assert metadata.checksum == "abc123"
        assert metadata.uploaded_by == "user-456"
        assert metadata.uploaded_at == now
        assert metadata.tenant_id == "tenant-789"

    def test_default_storage_key(self) -> None:
        """Test default storage key is empty."""
        metadata = FileMetadata(
            id="file-123",
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="abc123",
            uploaded_by="user-456",
            uploaded_at=datetime.now(UTC),
            tenant_id="tenant-789",
        )
        
        assert metadata.storage_key == ""

    def test_default_metadata_dict(self) -> None:
        """Test default metadata is empty dict."""
        metadata = FileMetadata(
            id="file-123",
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="abc123",
            uploaded_by="user-456",
            uploaded_at=datetime.now(UTC),
            tenant_id="tenant-789",
        )
        
        assert metadata.metadata == {}

    def test_with_custom_metadata(self) -> None:
        """Test with custom metadata."""
        metadata = FileMetadata(
            id="file-123",
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="abc123",
            uploaded_by="user-456",
            uploaded_at=datetime.now(UTC),
            tenant_id="tenant-789",
            storage_key="uploads/test.pdf",
            metadata={"category": "documents", "tags": ["important"]},
        )
        
        assert metadata.storage_key == "uploads/test.pdf"
        assert metadata.metadata["category"] == "documents"

    def test_immutability(self) -> None:
        """Test metadata is immutable."""
        metadata = FileMetadata(
            id="file-123",
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="abc123",
            uploaded_by="user-456",
            uploaded_at=datetime.now(UTC),
            tenant_id="tenant-789",
        )
        
        with pytest.raises(AttributeError):
            metadata.id = "new-id"  # type: ignore[misc]


class TestUploadResult:
    """Tests for UploadResult dataclass."""

    def test_creation(self) -> None:
        """Test result creation."""
        metadata = FileMetadata(
            id="file-123",
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="abc123",
            uploaded_by="user-456",
            uploaded_at=datetime.now(UTC),
            tenant_id="tenant-789",
        )
        
        result = UploadResult(
            file_id="file-123",
            storage_key="uploads/test.pdf",
            url="https://storage.example.com/uploads/test.pdf",
            metadata=metadata,
        )
        
        assert result.file_id == "file-123"
        assert result.storage_key == "uploads/test.pdf"
        assert result.url == "https://storage.example.com/uploads/test.pdf"
        assert result.metadata.filename == "test.pdf"

    def test_immutability(self) -> None:
        """Test result is immutable."""
        metadata = FileMetadata(
            id="file-123",
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum="abc123",
            uploaded_by="user-456",
            uploaded_at=datetime.now(UTC),
            tenant_id="tenant-789",
        )
        
        result = UploadResult(
            file_id="file-123",
            storage_key="uploads/test.pdf",
            url="https://example.com/test.pdf",
            metadata=metadata,
        )
        
        with pytest.raises(AttributeError):
            result.file_id = "new-id"  # type: ignore[misc]


class TestFileValidationConfig:
    """Tests for FileValidationConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = FileValidationConfig()
        
        assert config.max_size_bytes == 10 * 1024 * 1024  # 10MB
        assert config.scan_for_viruses is False

    def test_default_allowed_types(self) -> None:
        """Test default allowed MIME types."""
        config = FileValidationConfig()
        
        assert "image/jpeg" in config.allowed_types
        assert "image/png" in config.allowed_types
        assert "application/pdf" in config.allowed_types
        assert "text/plain" in config.allowed_types

    def test_default_allowed_extensions(self) -> None:
        """Test default allowed extensions."""
        config = FileValidationConfig()
        
        assert ".jpg" in config.allowed_extensions
        assert ".pdf" in config.allowed_extensions
        assert ".txt" in config.allowed_extensions

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = FileValidationConfig(
            max_size_bytes=5 * 1024 * 1024,
            allowed_types=frozenset({"image/jpeg", "image/png"}),
            allowed_extensions=frozenset({".jpg", ".png"}),
            scan_for_viruses=True,
        )
        
        assert config.max_size_bytes == 5 * 1024 * 1024
        assert len(config.allowed_types) == 2
        assert len(config.allowed_extensions) == 2
        assert config.scan_for_viruses is True

    def test_immutability(self) -> None:
        """Test config is immutable."""
        config = FileValidationConfig()
        
        with pytest.raises(AttributeError):
            config.max_size_bytes = 1024  # type: ignore[misc]
