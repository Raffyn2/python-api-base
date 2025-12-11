"""In-memory storage provider for testing.

**Feature: infrastructure-modules-workflow-analysis**
**Validates: Requirements 1.2**

Implements FileStorage protocol using in-memory storage.
Suitable for unit tests and development without external dependencies.
"""

from collections.abc import AsyncIterator
from datetime import timedelta

import structlog

from core.base.patterns.result import Err, Ok, Result

logger = structlog.get_logger(__name__)


class InMemoryStorageProvider:
    """In-memory implementation of FileStorage protocol.

    Useful for testing without external dependencies.

    **Feature: infrastructure-modules-workflow-analysis**
    **Validates: Requirements 1.2**
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._storage: dict[str, tuple[bytes, str]] = {}

    async def upload(
        self,
        key: str,
        data: bytes | AsyncIterator[bytes],
        content_type: str,
    ) -> Result[str, Exception]:
        """Upload file to memory.

        Args:
            key: Storage key/path.
            data: File data or async stream.
            content_type: MIME type.

        Returns:
            Ok with storage URL or Err with exception.
        """
        try:
            file_data = data if isinstance(data, bytes) else b"".join([chunk async for chunk in data])
            self._storage[key] = (file_data, content_type)

            logger.debug(
                "File uploaded to memory storage",
                operation="MEMORY_UPLOAD",
                key=key,
                content_type=content_type,
                size_bytes=len(file_data),
            )
            return Ok(f"memory://{key}")
        except Exception as e:
            logger.error(
                "Memory upload failed",
                operation="MEMORY_UPLOAD_ERROR",
                key=key,
                error_type=type(e).__name__,
            )
            return Err(e)

    async def download(self, key: str) -> Result[bytes, Exception]:
        """Download file from memory.

        Args:
            key: Storage key/path.

        Returns:
            Ok with file bytes or Err with exception.
        """
        if key not in self._storage:
            logger.warning(
                "File not found in memory storage",
                operation="MEMORY_DOWNLOAD_NOT_FOUND",
                key=key,
            )
            return Err(FileNotFoundError(f"Key not found: {key}"))

        data, _ = self._storage[key]
        logger.debug(
            "File downloaded from memory storage",
            operation="MEMORY_DOWNLOAD",
            key=key,
            size_bytes=len(data),
        )
        return Ok(data)

    async def delete(self, key: str) -> Result[bool, Exception]:
        """Delete file from memory.

        Args:
            key: Storage key/path.

        Returns:
            Ok with True if deleted, Err with exception.
        """
        if key in self._storage:
            del self._storage[key]
            logger.debug(
                "File deleted from memory storage",
                operation="MEMORY_DELETE",
                key=key,
            )
            return Ok(True)

        logger.debug(
            "File not found for deletion",
            operation="MEMORY_DELETE_NOT_FOUND",
            key=key,
        )
        return Ok(False)

    async def exists(self, key: str) -> bool:
        """Check if file exists in memory."""
        return key in self._storage

    async def generate_signed_url(
        self,
        key: str,
        expiration: timedelta,
        operation: str = "GET",
    ) -> Result[str, Exception]:
        """Generate signed URL (mock for testing).

        Args:
            key: Storage key/path.
            expiration: URL expiration time.
            operation: HTTP operation (GET, PUT).

        Returns:
            Ok with mock signed URL or Err with exception.
        """
        if key not in self._storage and operation == "GET":
            return Err(FileNotFoundError(f"Key not found: {key}"))

        return Ok(f"memory://{key}?signed=true&expires={int(expiration.total_seconds())}")

    def clear(self) -> None:
        """Clear all stored files."""
        self._storage.clear()

    @property
    def keys(self) -> list[str]:
        """Get all stored keys."""
        return list(self._storage.keys())


__all__ = ["InMemoryStorageProvider"]
