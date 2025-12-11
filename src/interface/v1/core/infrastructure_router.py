"""Infrastructure examples router (facade).

Aggregates cache, storage, and Kafka routers for backward compatibility.

**Feature: enterprise-infrastructure-2025**
**Refactored: Split into cache_router, storage_router, kafka_router for SRP**
"""

from __future__ import annotations

from fastapi import APIRouter

# Re-export DTOs for backward compatibility
from interface.v1.core.cache_router import (
    CacheResponse,
    CacheSetRequest,
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    cache_status,
    get_redis,
    router as cache_router,
)
from interface.v1.features.kafka_router import (
    KafkaPublishRequest,
    KafkaPublishResponse,
    KafkaStatusResponse,
    get_kafka,
    kafka_publish,
    kafka_status,
    router as kafka_router,
)
from interface.v1.features.storage_router import (
    PresignedUrlResponse,
    StorageUploadResponse,
    get_minio,
    router as storage_router,
    storage_delete,
    storage_download,
    storage_list,
    storage_presigned_url,
    storage_upload,
)

__all__ = [
    "CacheResponse",
    # Cache DTOs and functions
    "CacheSetRequest",
    # Kafka DTOs and functions
    "KafkaPublishRequest",
    "KafkaPublishResponse",
    "KafkaStatusResponse",
    "PresignedUrlResponse",
    # Storage DTOs and functions
    "StorageUploadResponse",
    "cache_delete",
    "cache_delete_pattern",
    "cache_get",
    "cache_set",
    "cache_status",
    "get_kafka",
    "get_minio",
    "get_redis",
    "kafka_publish",
    "kafka_status",
    "router",
    "storage_delete",
    "storage_download",
    "storage_list",
    "storage_presigned_url",
    "storage_upload",
]

# Create combined router
router = APIRouter(prefix="/infrastructure", tags=["Infrastructure Examples"])

# Include sub-routers
router.include_router(cache_router)
router.include_router(storage_router)
router.include_router(kafka_router)
