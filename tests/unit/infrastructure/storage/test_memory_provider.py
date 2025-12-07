"""Tests for infrastructure/storage/memory_provider.py - In-memory storage."""

from datetime import timedelta

import pytest

from src.infrastructure.storage.memory_provider import InMemoryStorageProvider


class TestInMemoryStorageProviderInit:
    """Tests for InMemoryStorageProvider initialization."""

    def test_init_creates_empty_storage(self):
        provider = InMemoryStorageProvider()
        assert provider.keys == []

    def test_init_storage_is_dict(self):
        provider = InMemoryStorageProvider()
        assert isinstance(provider._storage, dict)


class TestInMemoryStorageProviderUpload:
    """Tests for upload method."""

    @pytest.mark.asyncio
    async def test_upload_bytes_success(self):
        provider = InMemoryStorageProvider()
        result = await provider.upload("test.txt", b"hello world", "text/plain")
        assert result.is_ok()
        assert result.unwrap() == "memory://test.txt"

    @pytest.mark.asyncio
    async def test_upload_stores_data(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello world", "text/plain")
        assert "test.txt" in provider.keys

    @pytest.mark.asyncio
    async def test_upload_stores_content_type(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        data, content_type = provider._storage["test.txt"]
        assert content_type == "text/plain"

    @pytest.mark.asyncio
    async def test_upload_overwrites_existing(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"first", "text/plain")
        await provider.upload("test.txt", b"second", "text/plain")
        data, _ = provider._storage["test.txt"]
        assert data == b"second"

    @pytest.mark.asyncio
    async def test_upload_multiple_files(self):
        provider = InMemoryStorageProvider()
        await provider.upload("file1.txt", b"one", "text/plain")
        await provider.upload("file2.txt", b"two", "text/plain")
        assert len(provider.keys) == 2

    @pytest.mark.asyncio
    async def test_upload_with_path_key(self):
        provider = InMemoryStorageProvider()
        result = await provider.upload("folder/subfolder/file.txt", b"data", "text/plain")
        assert result.is_ok()
        assert result.unwrap() == "memory://folder/subfolder/file.txt"

    @pytest.mark.asyncio
    async def test_upload_binary_data(self):
        provider = InMemoryStorageProvider()
        binary_data = bytes(range(256))
        result = await provider.upload("binary.bin", binary_data, "application/octet-stream")
        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_upload_empty_data(self):
        provider = InMemoryStorageProvider()
        result = await provider.upload("empty.txt", b"", "text/plain")
        assert result.is_ok()


class TestInMemoryStorageProviderDownload:
    """Tests for download method."""

    @pytest.mark.asyncio
    async def test_download_existing_file(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello world", "text/plain")
        result = await provider.download("test.txt")
        assert result.is_ok()
        assert result.unwrap() == b"hello world"

    @pytest.mark.asyncio
    async def test_download_nonexistent_file(self):
        provider = InMemoryStorageProvider()
        result = await provider.download("nonexistent.txt")
        assert result.is_err()
        assert isinstance(result.error, FileNotFoundError)

    @pytest.mark.asyncio
    async def test_download_error_message(self):
        provider = InMemoryStorageProvider()
        result = await provider.download("missing.txt")
        assert "missing.txt" in str(result.error)

    @pytest.mark.asyncio
    async def test_download_binary_data(self):
        provider = InMemoryStorageProvider()
        binary_data = bytes(range(256))
        await provider.upload("binary.bin", binary_data, "application/octet-stream")
        result = await provider.download("binary.bin")
        assert result.is_ok()
        assert result.unwrap() == binary_data


class TestInMemoryStorageProviderDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        result = await provider.delete("test.txt")
        assert result.is_ok()
        assert result.unwrap() is True

    @pytest.mark.asyncio
    async def test_delete_removes_file(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        await provider.delete("test.txt")
        assert "test.txt" not in provider.keys

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self):
        provider = InMemoryStorageProvider()
        result = await provider.delete("nonexistent.txt")
        assert result.is_ok()
        assert result.unwrap() is False

    @pytest.mark.asyncio
    async def test_delete_one_of_many(self):
        provider = InMemoryStorageProvider()
        await provider.upload("file1.txt", b"one", "text/plain")
        await provider.upload("file2.txt", b"two", "text/plain")
        await provider.delete("file1.txt")
        assert "file1.txt" not in provider.keys
        assert "file2.txt" in provider.keys


class TestInMemoryStorageProviderExists:
    """Tests for exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        assert await provider.exists("test.txt") is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_nonexistent(self):
        provider = InMemoryStorageProvider()
        assert await provider.exists("nonexistent.txt") is False

    @pytest.mark.asyncio
    async def test_exists_after_delete(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        await provider.delete("test.txt")
        assert await provider.exists("test.txt") is False


class TestInMemoryStorageProviderSignedUrl:
    """Tests for generate_signed_url method."""

    @pytest.mark.asyncio
    async def test_signed_url_for_existing_file(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        result = await provider.generate_signed_url("test.txt", timedelta(hours=1))
        assert result.is_ok()
        url = result.unwrap()
        assert "memory://test.txt" in url
        assert "signed=true" in url

    @pytest.mark.asyncio
    async def test_signed_url_includes_expiration(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        result = await provider.generate_signed_url("test.txt", timedelta(hours=1))
        url = result.unwrap()
        assert "expires=3600" in url

    @pytest.mark.asyncio
    async def test_signed_url_different_expiration(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        result = await provider.generate_signed_url("test.txt", timedelta(minutes=30))
        url = result.unwrap()
        assert "expires=1800" in url

    @pytest.mark.asyncio
    async def test_signed_url_get_nonexistent_file(self):
        provider = InMemoryStorageProvider()
        result = await provider.generate_signed_url(
            "nonexistent.txt", timedelta(hours=1), operation="GET"
        )
        assert result.is_err()
        assert isinstance(result.error, FileNotFoundError)

    @pytest.mark.asyncio
    async def test_signed_url_put_nonexistent_file(self):
        provider = InMemoryStorageProvider()
        result = await provider.generate_signed_url(
            "new_file.txt", timedelta(hours=1), operation="PUT"
        )
        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_signed_url_default_operation_is_get(self):
        provider = InMemoryStorageProvider()
        result = await provider.generate_signed_url(
            "nonexistent.txt", timedelta(hours=1)
        )
        assert result.is_err()


class TestInMemoryStorageProviderClear:
    """Tests for clear method."""

    def test_clear_empty_storage(self):
        provider = InMemoryStorageProvider()
        provider.clear()
        assert provider.keys == []

    @pytest.mark.asyncio
    async def test_clear_removes_all_files(self):
        provider = InMemoryStorageProvider()
        await provider.upload("file1.txt", b"one", "text/plain")
        await provider.upload("file2.txt", b"two", "text/plain")
        await provider.upload("file3.txt", b"three", "text/plain")
        provider.clear()
        assert provider.keys == []

    @pytest.mark.asyncio
    async def test_clear_allows_new_uploads(self):
        provider = InMemoryStorageProvider()
        await provider.upload("old.txt", b"old", "text/plain")
        provider.clear()
        await provider.upload("new.txt", b"new", "text/plain")
        assert provider.keys == ["new.txt"]


class TestInMemoryStorageProviderKeys:
    """Tests for keys property."""

    def test_keys_empty_storage(self):
        provider = InMemoryStorageProvider()
        assert provider.keys == []

    @pytest.mark.asyncio
    async def test_keys_returns_list(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        assert isinstance(provider.keys, list)

    @pytest.mark.asyncio
    async def test_keys_contains_all_uploaded(self):
        provider = InMemoryStorageProvider()
        await provider.upload("file1.txt", b"one", "text/plain")
        await provider.upload("file2.txt", b"two", "text/plain")
        keys = provider.keys
        assert "file1.txt" in keys
        assert "file2.txt" in keys

    @pytest.mark.asyncio
    async def test_keys_is_copy(self):
        provider = InMemoryStorageProvider()
        await provider.upload("test.txt", b"hello", "text/plain")
        keys = provider.keys
        keys.append("fake.txt")
        assert "fake.txt" not in provider.keys


class TestInMemoryStorageProviderIntegration:
    """Integration tests for InMemoryStorageProvider."""

    @pytest.mark.asyncio
    async def test_upload_download_cycle(self):
        provider = InMemoryStorageProvider()
        original_data = b"test data for upload/download cycle"
        await provider.upload("cycle.txt", original_data, "text/plain")
        result = await provider.download("cycle.txt")
        assert result.unwrap() == original_data

    @pytest.mark.asyncio
    async def test_upload_delete_download_fails(self):
        provider = InMemoryStorageProvider()
        await provider.upload("temp.txt", b"temporary", "text/plain")
        await provider.delete("temp.txt")
        result = await provider.download("temp.txt")
        assert result.is_err()

    @pytest.mark.asyncio
    async def test_multiple_operations_sequence(self):
        provider = InMemoryStorageProvider()
        
        # Upload
        await provider.upload("file.txt", b"v1", "text/plain")
        assert await provider.exists("file.txt")
        
        # Download
        result = await provider.download("file.txt")
        assert result.unwrap() == b"v1"
        
        # Update (overwrite)
        await provider.upload("file.txt", b"v2", "text/plain")
        result = await provider.download("file.txt")
        assert result.unwrap() == b"v2"
        
        # Delete
        await provider.delete("file.txt")
        assert not await provider.exists("file.txt")
