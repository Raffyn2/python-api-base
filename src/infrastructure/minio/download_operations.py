"""MinIO download operations.

**Feature: enterprise-infrastructure-2025**
**Refactored: 2025 - Extracted from client.py for SRP compliance**
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from core.base.patterns.result import Err, Ok

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from core.base.patterns.result import Result

logger = structlog.get_logger(__name__)


class DownloadOperations:
    """MinIO download operations handler."""

    def __init__(self, client: Any, default_bucket: str) -> None:
        """Initialize download operations."""
        self._client = client
        self._default_bucket = default_bucket

    async def download(
        self,
        key: str,
        bucket: str | None = None,
    ) -> Result[bytes, Exception]:
        """Download object.

        **Requirement: R3.4 - Streaming download**
        """
        target_bucket = bucket or self._default_bucket

        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                target_bucket,
                key,
            )

            try:
                data = response.read()
                return Ok(data)
            finally:
                response.close()
                response.release_conn()

        except Exception as e:
            logger.exception(
                "Download failed",
                key=key,
                operation="MINIO_DOWNLOAD",
            )
            return Err(e)

    async def download_stream(
        self,
        key: str,
        bucket: str | None = None,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """Download object as async stream."""
        target_bucket = bucket or self._default_bucket

        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                target_bucket,
                key,
            )

            try:
                for chunk in response.stream(chunk_size):
                    yield chunk
            finally:
                response.close()
                response.release_conn()

        except Exception:
            logger.exception(
                "Stream download failed",
                operation="MINIO_STREAM_DOWNLOAD",
            )
