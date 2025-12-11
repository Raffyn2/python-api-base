"""MinIO storage provider implementation.

**Feature: infrastructure-modules-workflow-analysis**
**Validates: Requirements 1.2**

Implements FileStorage protocol using MinIO client.
"""

from collections.abc import AsyncIterator
from datetime import timedelta

import structlog

from core.base.patterns.result import Err, Ok, Result
from infrastructure.minio import MinIOClient

logger = structlog.get_logger(__name__)


class MinIOStorageProvider:
    """MinIO implementation of FileStorage protocol.

    **Feature: infrastructure-modules-workflow-analysis**
    **Validates: Requirements 1.2**
    """

    def __init__(self, client: MinIOClient) -> None:
        """Initialize MinIO storage provider.

        Args:
            client: MinIO client instance.
        """
        self._client = client

    async def upload(
        self,
        key: str,
        data: bytes | AsyncIterator[bytes],
        content_type: str,
    ) -> Result[str, Exception]:
        """Upload file to MinIO.

        Args:
            key: Storage key/path.
            data: File data or async stream.
            content_type: MIME type.

        Returns:
            Ok with storage URL or Err with exception.
        """
        try:
            if isinstance(data, bytes):
                await self._client.upload_bytes(key, data, content_type)
            else:
                # Collect async iterator to bytes
                collected = b"".join([chunk async for chunk in data])
                await self._client.upload_bytes(key, collected, content_type)

            # Generate a short-lived URL for the uploaded object
            url = await self._client.get_presigned_url(key, expires=3600)

            logger.debug(
                "File uploaded to MinIO",
                operation="MINIO_UPLOAD",
                key=key,
                content_type=content_type,
            )
            return Ok(url)
        except Exception as e:
            logger.error(
                "MinIO upload failed",
                operation="MINIO_UPLOAD_ERROR",
                key=key,
                error_type=type(e).__name__,
            )
            return Err(e)

    async def download(self, key: str) -> Result[bytes, Exception]:
        """Download file from MinIO.

        Args:
            key: Storage key/path.

        Returns:
            Ok with file bytes or Err with exception.
        """
        try:
            data = await self._client.download_bytes(key)
            logger.debug(
                "File downloaded from MinIO",
                operation="MINIO_DOWNLOAD",
                key=key,
                size_bytes=len(data),
            )
            return Ok(data)
        except Exception as e:
            logger.error(
                "MinIO download failed",
                operation="MINIO_DOWNLOAD_ERROR",
                key=key,
                error_type=type(e).__name__,
            )
            return Err(e)

    async def delete(self, key: str) -> Result[bool, Exception]:
        """Delete file from MinIO.

        Args:
            key: Storage key/path.

        Returns:
            Ok with True if deleted, Err with exception.
        """
        try:
            await self._client.delete(key)
            logger.debug(
                "File deleted from MinIO",
                operation="MINIO_DELETE",
                key=key,
            )
            return Ok(True)
        except Exception as e:
            logger.error(
                "MinIO delete failed",
                operation="MINIO_DELETE_ERROR",
                key=key,
                error_type=type(e).__name__,
            )
            return Err(e)

    async def exists(self, key: str) -> bool:
        """Check if file exists in MinIO."""
        try:
            return await self._client.exists(key)
        except Exception:
            return False

    async def generate_signed_url(
        self,
        key: str,
        expiration: timedelta,
        operation: str = "GET",
    ) -> Result[str, Exception]:
        """Generate signed URL for file access.

        Args:
            key: Storage key/path.
            expiration: URL expiration time.
            operation: HTTP operation (GET, PUT).

        Returns:
            Ok with signed URL or Err with exception.
        """
        try:
            url = await self._client.get_presigned_url(
                key,
                expires=int(expiration.total_seconds()),
                method=operation,
            )
            logger.debug(
                "Signed URL generated",
                operation="MINIO_SIGNED_URL",
                key=key,
                http_operation=operation,
                expiration_seconds=int(expiration.total_seconds()),
            )
            return Ok(url)
        except Exception as e:
            logger.error(
                "MinIO signed URL generation failed",
                operation="MINIO_SIGNED_URL_ERROR",
                key=key,
                error_type=type(e).__name__,
            )
            return Err(e)


__all__ = ["MinIOStorageProvider"]
