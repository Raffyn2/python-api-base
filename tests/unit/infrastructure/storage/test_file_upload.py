"""Unit tests for file upload handling.

Tests FileInfo, UploadProgress, FileValidationRules, and ConfigurableFileValidator.
"""

import pytest
from pydantic import BaseModel

from core.base.patterns.result import Err, Ok
from infrastructure.storage.file_upload import (
    ChunkInfo,
    ConfigurableFileValidator,
    FileInfo,
    FileValidationRules,
    UploadProgress,
)


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_creation(self) -> None:
        """Test FileInfo creation."""
        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
            checksum="abc123",
        )

        assert info.filename == "test.txt"
        assert info.content_type == "text/plain"
        assert info.size_bytes == 1024
        assert info.checksum == "abc123"

    def test_default_checksum(self) -> None:
        """Test FileInfo with default checksum."""
        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
        )

        assert info.checksum is None


class TestUploadProgress:
    """Tests for UploadProgress dataclass."""

    def test_creation(self) -> None:
        """Test UploadProgress creation."""
        progress = UploadProgress(
            bytes_uploaded=500,
            total_bytes=1000,
            chunks_completed=1,
            total_chunks=2,
        )

        assert progress.bytes_uploaded == 500
        assert progress.total_bytes == 1000
        assert progress.chunks_completed == 1
        assert progress.total_chunks == 2

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
        """Test percentage at 100%."""
        progress = UploadProgress(
            bytes_uploaded=1000,
            total_bytes=1000,
            chunks_completed=2,
            total_chunks=2,
        )

        assert progress.percentage == 100.0


class TestFileValidationRules:
    """Tests for FileValidationRules dataclass."""

    def test_default_values(self) -> None:
        """Test default validation rules."""
        rules = FileValidationRules()

        assert rules.allowed_extensions == set()
        assert rules.allowed_content_types == set()
        assert rules.max_size_bytes == 10 * 1024 * 1024
        assert rules.min_size_bytes == 1

    def test_custom_values(self) -> None:
        """Test custom validation rules."""
        rules = FileValidationRules(
            allowed_extensions={"jpg", "png"},
            allowed_content_types={"image/jpeg", "image/png"},
            max_size_bytes=5 * 1024 * 1024,
            min_size_bytes=100,
        )

        assert rules.allowed_extensions == {"jpg", "png"}
        assert rules.allowed_content_types == {"image/jpeg", "image/png"}
        assert rules.max_size_bytes == 5 * 1024 * 1024
        assert rules.min_size_bytes == 100


class TestConfigurableFileValidator:
    """Tests for ConfigurableFileValidator."""

    @pytest.fixture
    def validator(self) -> ConfigurableFileValidator[None]:
        """Create validator with test rules."""
        rules = FileValidationRules(
            allowed_extensions={"jpg", "png", "pdf"},
            allowed_content_types={"image/jpeg", "image/png", "application/pdf"},
            max_size_bytes=5 * 1024 * 1024,
            min_size_bytes=100,
        )
        return ConfigurableFileValidator[None](rules)

    def test_valid_file(self, validator: ConfigurableFileValidator[None]) -> None:
        """Test validation of valid file."""
        info = FileInfo(
            filename="test.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
        )

        result = validator.validate(info)

        assert result.is_ok()
        assert result.unwrap() == info

    def test_file_too_small(self, validator: ConfigurableFileValidator[None]) -> None:
        """Test validation rejects too small file."""
        info = FileInfo(
            filename="test.jpg",
            content_type="image/jpeg",
            size_bytes=50,
        )

        result = validator.validate(info)

        assert result.is_err()
        assert "too small" in result.error.lower()

    def test_file_too_large(self, validator: ConfigurableFileValidator[None]) -> None:
        """Test validation rejects too large file."""
        info = FileInfo(
            filename="test.jpg",
            content_type="image/jpeg",
            size_bytes=10 * 1024 * 1024,
        )

        result = validator.validate(info)

        assert result.is_err()
        assert "too large" in result.error.lower()

    def test_invalid_extension(
        self, validator: ConfigurableFileValidator[None]
    ) -> None:
        """Test validation rejects invalid extension."""
        info = FileInfo(
            filename="test.exe",
            content_type="application/octet-stream",
            size_bytes=1024,
        )

        result = validator.validate(info)

        assert result.is_err()
        assert "extension not allowed" in result.error.lower()

    def test_invalid_content_type(
        self, validator: ConfigurableFileValidator[None]
    ) -> None:
        """Test validation rejects invalid content type."""
        info = FileInfo(
            filename="test.jpg",
            content_type="text/plain",
            size_bytes=1024,
        )

        result = validator.validate(info)

        assert result.is_err()
        assert "content type not allowed" in result.error.lower()

    def test_no_extension_rules(self) -> None:
        """Test validation without extension rules."""
        rules = FileValidationRules(
            max_size_bytes=5 * 1024 * 1024,
            min_size_bytes=100,
        )
        validator = ConfigurableFileValidator[None](rules)
        info = FileInfo(
            filename="test.anything",
            content_type="application/octet-stream",
            size_bytes=1024,
        )

        result = validator.validate(info)

        assert result.is_ok()

    def test_no_content_type_rules(self) -> None:
        """Test validation without content type rules."""
        rules = FileValidationRules(
            allowed_extensions={"txt"},
            max_size_bytes=5 * 1024 * 1024,
            min_size_bytes=100,
        )
        validator = ConfigurableFileValidator[None](rules)
        info = FileInfo(
            filename="test.txt",
            content_type="anything/anything",
            size_bytes=1024,
        )

        result = validator.validate(info)

        assert result.is_ok()


class TestChunkInfo:
    """Tests for ChunkInfo dataclass."""

    def test_creation(self) -> None:
        """Test ChunkInfo creation."""
        chunk = ChunkInfo(
            chunk_number=1,
            total_chunks=5,
            chunk_size=1024,
            offset=0,
        )

        assert chunk.chunk_number == 1
        assert chunk.total_chunks == 5
        assert chunk.chunk_size == 1024
        assert chunk.offset == 0



class MockStorage:
    """Mock storage for testing FileUploadHandler."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
    ) -> Ok[str] | Err[Exception]:
        """Mock upload."""
        self._files[key] = data if isinstance(data, bytes) else b""
        return Ok(f"https://storage.example.com/{key}")

    async def download(self, key: str) -> Ok[bytes] | Err[Exception]:
        """Mock download."""
        if key in self._files:
            return Ok(self._files[key])
        return Err(FileNotFoundError(f"File not found: {key}"))

    async def delete(self, key: str) -> Ok[bool] | Err[Exception]:
        """Mock delete."""
        if key in self._files:
            del self._files[key]
            return Ok(True)
        return Ok(False)

    async def exists(self, key: str) -> bool:
        """Mock exists."""
        return key in self._files

    async def generate_signed_url(
        self,
        key: str,
        expiration: "timedelta",
        operation: str = "GET",
    ) -> Ok[str] | Err[Exception]:
        """Mock signed URL generation."""
        from datetime import timedelta

        return Ok(f"https://storage.example.com/{key}?signed=true")


class MockFailingStorage:
    """Mock storage that fails on upload."""

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
    ) -> Ok[str] | Err[Exception]:
        """Mock failing upload."""
        return Err(Exception("Storage error"))

    async def download(self, key: str) -> Ok[bytes] | Err[Exception]:
        """Mock download."""
        return Err(FileNotFoundError("Not found"))

    async def delete(self, key: str) -> Ok[bool] | Err[Exception]:
        """Mock delete."""
        return Err(Exception("Delete error"))

    async def exists(self, key: str) -> bool:
        """Mock exists."""
        return False

    async def generate_signed_url(
        self,
        key: str,
        expiration: "timedelta",
        operation: str = "GET",
    ) -> Ok[str] | Err[Exception]:
        """Mock signed URL generation."""
        return Err(Exception("URL generation error"))


class TestFileUploadHandler:
    """Tests for FileUploadHandler."""

    @pytest.fixture
    def storage(self) -> MockStorage:
        """Create mock storage."""
        return MockStorage()

    @pytest.fixture
    def handler(self, storage: MockStorage) -> "FileUploadHandler[None]":
        """Create upload handler."""
        from infrastructure.storage.file_upload import FileUploadHandler

        return FileUploadHandler[None](storage=storage)

    @pytest.mark.asyncio
    async def test_upload_success(
        self, handler: "FileUploadHandler[None]"
    ) -> None:
        """Test successful file upload."""
        from infrastructure.storage.file_upload import FileUploadHandler

        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=11,
        )

        result = await handler.upload(
            upload_id="upload-123",
            file_info=info,
            data=b"hello world",
        )

        assert result.is_ok()
        assert "test.txt" in result.unwrap()

    @pytest.mark.asyncio
    async def test_upload_with_validator(self, storage: MockStorage) -> None:
        """Test upload with validator."""
        from infrastructure.storage.file_upload import (
            ConfigurableFileValidator,
            FileUploadHandler,
            FileValidationRules,
        )

        rules = FileValidationRules(
            allowed_extensions={"txt"},
            max_size_bytes=1024,
            min_size_bytes=1,
        )
        validator = ConfigurableFileValidator[None](rules)
        handler = FileUploadHandler[None](storage=storage, validator=validator)

        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=11,
        )

        result = await handler.upload(
            upload_id="upload-123",
            file_info=info,
            data=b"hello world",
        )

        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_upload_validation_failure(self, storage: MockStorage) -> None:
        """Test upload fails validation."""
        from infrastructure.storage.file_upload import (
            ConfigurableFileValidator,
            FileUploadHandler,
            FileValidationRules,
        )

        rules = FileValidationRules(
            allowed_extensions={"pdf"},
            max_size_bytes=1024,
            min_size_bytes=1,
        )
        validator = ConfigurableFileValidator[None](rules)
        handler = FileUploadHandler[None](storage=storage, validator=validator)

        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=11,
        )

        result = await handler.upload(
            upload_id="upload-123",
            file_info=info,
            data=b"hello world",
        )

        assert result.is_err()
        assert "extension not allowed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_upload_storage_failure(self) -> None:
        """Test upload handles storage failure."""
        from infrastructure.storage.file_upload import FileUploadHandler

        storage = MockFailingStorage()
        handler = FileUploadHandler[None](storage=storage)

        info = FileInfo(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=11,
        )

        result = await handler.upload(
            upload_id="upload-123",
            file_info=info,
            data=b"hello world",
        )

        assert result.is_err()
        assert "Storage error" in result.error

    @pytest.mark.asyncio
    async def test_upload_chunk(
        self, handler: "FileUploadHandler[None]"
    ) -> None:
        """Test chunk upload."""
        from infrastructure.storage.file_upload import ChunkInfo

        chunk_info = ChunkInfo(
            chunk_number=1,
            total_chunks=3,
            chunk_size=1024,
            offset=0,
        )

        result = await handler.upload_chunk(
            upload_id="upload-123",
            chunk=b"chunk data",
            chunk_info=chunk_info,
        )

        assert result.is_ok()
        progress = result.unwrap()
        assert progress.chunks_completed == 1
        assert progress.total_chunks == 3

    @pytest.mark.asyncio
    async def test_upload_multiple_chunks(
        self, handler: "FileUploadHandler[None]"
    ) -> None:
        """Test multiple chunk uploads."""
        from infrastructure.storage.file_upload import ChunkInfo

        for i in range(3):
            chunk_info = ChunkInfo(
                chunk_number=i + 1,
                total_chunks=3,
                chunk_size=1024,
                offset=i * 1024,
            )
            result = await handler.upload_chunk(
                upload_id="upload-123",
                chunk=b"chunk data",
                chunk_info=chunk_info,
            )
            assert result.is_ok()

        progress = handler.get_progress("upload-123")
        assert progress is not None
        assert progress.chunks_completed == 3

    def test_get_progress_not_found(
        self, handler: "FileUploadHandler[None]"
    ) -> None:
        """Test get_progress returns None for unknown upload."""
        progress = handler.get_progress("unknown")

        assert progress is None

    @pytest.mark.asyncio
    async def test_generate_download_url(
        self, handler: "FileUploadHandler[None]"
    ) -> None:
        """Test generate download URL."""
        from datetime import timedelta

        result = await handler.generate_download_url(
            key="uploads/test.txt",
            expiration=timedelta(hours=1),
        )

        assert result.is_ok()
        assert "signed=true" in result.unwrap()
