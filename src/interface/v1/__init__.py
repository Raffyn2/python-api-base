"""API v1 routers.

**Feature: architecture-restructuring-2025**
**Validates: Requirements 5.1**
"""

from interface.v1.cache_router import router as cache_router
from interface.v1.health_router import router as health_router
from interface.v1.infrastructure_router import router as infrastructure_router
from interface.v1.kafka_router import router as kafka_router
from interface.v1.storage_router import router as storage_router
from interface.v1.users_router import router as users_router

__all__ = [
    "cache_router",
    "health_router",
    "infrastructure_router",
    "kafka_router",
    "storage_router",
    "users_router",
]
