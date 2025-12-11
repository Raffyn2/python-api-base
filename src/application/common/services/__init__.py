"""Reusable services for application layer.

Application services.

Organized into subpackages by responsibility:
- cache/: Cache service implementations
- events/: Event service implementations
- generic_service: Generic CRUD service base class

**Feature: architecture-restructuring-2025**
**Feature: python-api-base-2025-validation**
"""

from application.common.services.cache import CacheService
from application.common.services.events import KafkaEventService
from application.common.services.generic_service import GenericService
from application.common.services.protocols import IEventBus, IEventPublisher, IServiceMapper
from application.common.services.service_errors import (
    ConflictError,
    DeleteError,
    NotFoundError,
    ServiceError,
    ValidationError,
)

__all__ = [
    # Cache
    "CacheService",
    # Errors
    "ConflictError",
    "DeleteError",
    # Generic Service
    "GenericService",
    # Protocols
    "IEventBus",
    "IEventPublisher",
    "IServiceMapper",
    # Events
    "KafkaEventService",
    "NotFoundError",
    "ServiceError",
    "ValidationError",
]
