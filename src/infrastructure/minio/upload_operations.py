"""MinIO upload operations.

**Feature: enterprise-infrastructure-2025**
**Refactored: 2025 - Extracted from client.py for SRP compliance**
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Any

import structlog

from core.base.patterns.result import Err, Ok

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from core.base.patterns.result import Result

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class UploadProgress:
    """Progress information for multipart upload."""

    uploaded_bytes: int
    total_bytes: int
    parts_completed: int
    total_parts: int

    @property
    def percentage(self) -> float:
        """Get upload progress percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.uploaded_bytes / self.total_bytes) * 100


class UploadOperations:
    """MinIO upload operations handler."""

    def __init__(
        self,
        client: Any,
        default_bucket: str,
        max_file_size: int,
        allowed_content_types: list[str] | None,
    ) -> None:
        """Initialize upload operations."""
        self._client = client
        self._default_bucket = default_bucket
        self._max_file_size = max_file_size
        self._allowed_content_types = allowed_content_types

    async def upload(
        self,
        key: str,
        data: bytes | BytesIO,
        content_type: str,
        metadata: dict[str, str] | None = None,
        bucket: str | None = None,
    ) -> Result[str, Exception]:
        """Upload object to storage.

        **Requirement: R3.2 - Streaming upload with progress**
        """
        target_bucket = bucket or self._default_bucket

        try:
            if isinstance(data, bytes):
                data = BytesIO(data)

            size = data.seek(0, 2)
            data.seek(0)

            if size > self._max_file_size:
                return Err(ValueError(f"File too large: {size} > {self._max_file_size}"))

            if self._allowed_content_types and content_type not in self._allowed_content_types:
                return Err(ValueError(f"Content type not allowed: {content_type}"))

            await asyncio.to_thread(
                self._client.put_object,
                target_bucket,
                key,
                data,
                size,
                content_type=content_type,
                metadata=metadata,
            )

            url = f"s3://{target_bucket}/{key}"
            logger.info(
                "Object uploaded",
                bucket=target_bucket,
                key=key,
                size=size,
            )
            return Ok(url)

        except Exception as e:
            logger.exception(
                "Upload failed",
                key=key,
                operation="MINIO_UPLOAD",
            )
            return Err(e)

    async def upload_stream(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        content_type: str,
        total_size: int,
        metadata: dict[str, str] | None = None,
        bucket: str | None = None,
        progress_callback: Any | None = None,
    ) -> Result[str, Exception]:
        """Upload from async stream.

        **Requirement: R3.3 - Multipart upload**
        """
        target_bucket = bucket or self._default_bucket

        try:
            buffer = BytesIO()
            uploaded = 0

            async for chunk in stream:
                buffer.write(chunk)
                uploaded += len(chunk)

                if progress_callback:
                    progress = UploadProgress(
                        uploaded_bytes=uploaded,
                        total_bytes=total_size,
                        parts_completed=0,
                        total_parts=1,
                    )
                    await progress_callback(progress)

            buffer.seek(0)

            await asyncio.to_thread(
                self._client.put_object,
                target_bucket,
                key,
                buffer,
                uploaded,
                content_type=content_type,
                metadata=metadata,
            )

            url = f"s3://{target_bucket}/{key}"
            return Ok(url)

        except Exception as e:
            logger.exception(
                "Stream upload failed",
                key=key,
                operation="MINIO_STREAM_UPLOAD",
            )
            return Err(e)
