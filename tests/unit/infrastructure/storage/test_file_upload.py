"""Unit tests for file upload handling.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5**
"""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from core.base.patterns.result import Err, Ok
from infrastructure.storage.file_upload import (
    ChunkInfo,
    ConfigurableFileValidator,
    FileInfo,
    FileUploadHandler,
    FileValidationRules,
    UploadProgress,
)


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_create_file_info(self) -> None:
        """Test creating FileInfo."""
        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
        )

        assert info.filename == "test.txt"
        assert info.content_type == "text/plain"
        assert info.size_bytes == 1024
        assert info.checksum is None

    def test_file_info_with_checksum(self) -> None:
        """Test FileInfo with checksum."""
        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
            checksum="abc123",
        )

        assert info.checksum == "abc123"


class TestUploadProgress:
    """Tests for UploadProgress dataclass."""

    def test_percentage_calculation(self) -> None:
        """Test percentage calculation."""
        progress = UploadProgress(
            bytes_uploaded=500,
            total_bytes=1000,
            chunks_completed=1,
            total_chunks=2,
        )

        assert progress.percentage == 50.0

    def test_percentage_zero_total(self) -> None:
        """Test percentage with zero total bytes."""
        progress = UploadProgress(
            bytes_uploaded=0,
            total_bytes=0,
            chunks_completed=0,
            total_chunks=0,
        )

        assert progress.percentage == 0.0

    def test_percentage_complete(self) -> None:
        """Test 100% completion."""
        progress = UploadProgress(
            bytes_uploaded=1000,
            total_bytes=1000,
            chunks_completed=2,
            total_chunks=2,
        )

        assert progress.percentage == 100.0


class TestFileValidationRules:
    """Tests for FileValidationRules."""

    def test_default_rules(self) -> None:
        """Test default validation rules."""
        rules = FileValidationRules()

        assert rules.max_size_bytes == 10 * 1024 * 1024
        assert rules.min_size_bytes == 1
        assert rules.allowed_extensions == set()
        assert rules.allowed_content_types == set()

    def test_custom_rules(self) -> None:
        """Test custom validation rules."""
        rules = FileValidationRules(
            allowed_extensions={"txt", "pdf"},
            max_size_bytes=5 * 1024 * 1024,
        )

        assert rules.allowed_extensions == {"txt", "pdf"}
        assert rules.max_size_bytes == 5 * 1024 * 1024


class TestConfigurableFileValidator:
    """Tests for ConfigurableFileValidator."""

    @pytest.fixture
    def rules(self) -> FileValidationRules:
        """Create validation rules."""
        return FileValidationRules(
            allowed_extensions={"txt", "pdf"},
            allowed_content_types={"text/plain", "application/pdf"},
            max_size_bytes=1024 * 1024,
            min_size_bytes=10,
        )

    @pytest.fixture
    def validator(self, rules: FileValidationRules) -> ConfigurableFileValidator[None]:
        """Create validator."""
        return ConfigurableFileValidator[None](rules)

    def test_valid_file(self, validator: ConfigurableFileValidator[None]) -> None:
        """Test valid file passes validation."""
        file_info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=500,
        )

        result = validator.validate(file_info)

        assert result.is_ok()
        assert result.unwrap() == file_info

    def test_file_too_small(self, validator: ConfigurableFileValidator[None]) -> None:
        """Test file too small fails."""
        file_info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=5,
        )

        result = validator.validate(file_info)

        assert result.is_err()
        assert "too small" in result.error

    def test_file_too_large(self, validator: ConfigurableFileValidator[None]) -> None:
        """Test file too large fails."""
        file_info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=2 * 1024 * 1024,
        )

        result = validator.validate(file_info)

        assert result.is_err()
        assert "too large" in result.error

    def test_extension_not_allowed(
        self, validator: ConfigurableFileValidator[None]
    ) -> None:
        """Test disallowed extension fails."""
        file_info = FileInfo(
            filename="test.exe",
            content_type="application/octet-stream",
            size_bytes=500,
        )

        result = validator.validate(file_info)

        assert result.is_err()
        assert "Extension not allowed" in result.error

    def test_content_type_not_allowed(
        self, validator: ConfigurableFileValidator[None]
    ) -> None:
        """Test disallowed content type fails."""
        file_info = FileInfo(
            filename="test.txt",
            content_type="application/octet-stream",
            size_bytes=500,
        )

        result = validator.validate(file_info)

        assert result.is_err()
        assert "Content type not allowed" in result.error

    def test_no_extension_rules(self) -> None:
        """Test validation without extension rules."""
        rules = FileValidationRules()
        validator = ConfigurableFileValidator[None](rules)

        file_info = FileInfo(
            filename="test.exe",
            content_type="application/octet-stream",
            size_bytes=500,
        )

        result = validator.validate(file_info)

        assert result.is_ok()


class TestFileUploadHandler:
    """Tests for FileUploadHandler."""

    class TestMetadata(BaseModel):
        """Test metadata model."""

        description: str

    @pytest.fixture
    def mock_storage(self) -> AsyncMock:
        """Create mock storage."""
        storage = AsyncMock()
        storage.upload = AsyncMock(return_value=Ok("https://storage/file.txt"))
        storage.download = AsyncMock(return_value=Ok(b"content"))
        storage.delete = AsyncMock(return_value=Ok(True))
        storage.exists = AsyncMock(return_value=True)
        storage.generate_signed_url = AsyncMock(
            return_value=Ok("https://signed-url")
        )
        return storage

    @pytest.fixture
    def handler(self, mock_storage: AsyncMock) -> FileUploadHandler[TestMetadata]:
        """Create upload handler."""
        return FileUploadHandler[TestFileUploadHandler.TestMetadata](mock_storage)

    @pytest.fixture
    def file_info(self) -> FileInfo:
        """Create file info."""
        return FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
        )

    @pytest.mark.asyncio
    async def test_upload_success(
        self,
        handler: FileUploadHandler[TestMetadata],
        file_info: FileInfo,
    ) -> None:
        """Test successful upload."""
        result = await handler.upload("upload-1", file_info, b"content")

        assert result.is_ok()
        assert "https://storage" in result.unwrap()

    @pytest.mark.asyncio
    async def test_upload_with_metadata(
        self,
        handler: FileUploadHandler[TestMetadata],
        file_info: FileInfo,
    ) -> None:
        """Test upload with metadata."""
        metadata = TestFileUploadHandler.TestMetadata(description="Test file")

        result = await handler.upload("upload-1", file_info, b"content", metadata)

        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_upload_with_validator_success(
        self, mock_storage: AsyncMock, file_info: FileInfo
    ) -> None:
        """Test upload with passing validation."""
        rules = FileValidationRules(
            allowed_extensions={"txt"},
            allowed_content_types={"text/plain"},
        )
        validator = ConfigurableFileValidator[None](rules)
        handler = FileUploadHandler[None](mock_storage, validator=validator)

        result = await handler.upload("upload-1", file_info, b"content")

        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_upload_with_validator_failure(
        self, mock_storage: AsyncMock
    ) -> None:
        """Test upload with failing validation."""
        rules = FileValidationRules(allowed_extensions={"pdf"})
        validator = ConfigurableFileValidator[None](rules)
        handler = FileUploadHandler[None](mock_storage, validator=validator)

        file_info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
        )

        result = await handler.upload("upload-1", file_info, b"content")

        assert result.is_err()
        assert "Extension not allowed" in result.error

    @pytest.mark.asyncio
    async def test_upload_storage_error(
        self, mock_storage: AsyncMock, file_info: FileInfo
    ) -> None:
        """Test upload with storage error."""
        mock_storage.upload.return_value = Err(Exception("Storage error"))
        handler = FileUploadHandler[None](mock_storage)

        result = await handler.upload("upload-1", file_info, b"content")

        assert result.is_err()
        assert "Storage error" in result.error

    @pytest.mark.asyncio
    async def test_upload_chunk(
        self, handler: FileUploadHandler[TestMetadata]
    ) -> None:
        """Test chunk upload."""
        chunk_info = ChunkInfo(
            chunk_number=1,
            total_chunks=3,
            chunk_size=1024,
            offset=0,
        )

        result = await handler.upload_chunk("upload-1", b"chunk-data", chunk_info)

        assert result.is_ok()
        progress = result.unwrap()
        assert progress.chunks_completed == 1

    @pytest.mark.asyncio
    async def test_upload_multiple_chunks(
        self, handler: FileUploadHandler[TestMetadata]
    ) -> None:
        """Test multiple chunk uploads."""
        for i in range(3):
            chunk_info = ChunkInfo(
                chunk_number=i + 1,
                total_chunks=3,
                chunk_size=1024,
                offset=i * 1024,
            )
            result = await handler.upload_chunk("upload-1", b"chunk-data", chunk_info)
            assert result.is_ok()

        progress = handler.get_progress("upload-1")
        assert progress is not None
        assert progress.chunks_completed == 3

    @pytest.mark.asyncio
    async def test_upload_chunk_storage_error(
        self, mock_storage: AsyncMock
    ) -> None:
        """Test chunk upload with storage error."""
        mock_storage.upload.return_value = Err(Exception("Storage error"))
        handler = FileUploadHandler[None](mock_storage)

        chunk_info = ChunkInfo(
            chunk_number=1,
            total_chunks=3,
            chunk_size=1024,
            offset=0,
        )

        result = await handler.upload_chunk("upload-1", b"chunk-data", chunk_info)

        assert result.is_err()

    def test_get_progress_nonexistent(
        self, handler: FileUploadHandler[TestMetadata]
    ) -> None:
        """Test getting progress for nonexistent upload."""
        progress = handler.get_progress("nonexistent")
        assert progress is None

    @pytest.mark.asyncio
    async def test_generate_download_url(
        self, handler: FileUploadHandler[TestMetadata]
    ) -> None:
        """Test generating download URL."""
        result = await handler.generate_download_url("file.txt")

        assert result.is_ok()
        assert "signed-url" in result.unwrap()

    @pytest.mark.asyncio
    async def test_generate_download_url_custom_expiration(
        self, handler: FileUploadHandler[TestMetadata], mock_storage: AsyncMock
    ) -> None:
        """Test generating download URL with custom expiration."""
        await handler.generate_download_url("file.txt", timedelta(hours=24))

        mock_storage.generate_signed_url.assert_called_with(
            "file.txt", timedelta(hours=24), "GET"
        )
