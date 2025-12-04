"""Infrastructure error hierarchy.

**Feature: infrastructure-code-review**
**Validates: Requirements 8.2, 10.3**

Provides a structured exception hierarchy for consistent error handling
across all infrastructure modules.
"""

from infrastructure.errors.base import InfrastructureError
from infrastructure.errors.database import (
    ConnectionPoolError,
    DatabaseError,
)
from infrastructure.errors.external import (
    CacheError,
    ExternalServiceError,
    MessagingError,
    StorageError,
)
from infrastructure.errors.security import (
    AuditLogError,
    TokenStoreError,
    TokenValidationError,
)
from infrastructure.errors.system import (
    ConfigurationError,
    TelemetryError,
)

__all__ = [
    "AuditLogError",
    "CacheError",
    "ConfigurationError",
    "ConnectionPoolError",
    # Database
    "DatabaseError",
    # External
    "ExternalServiceError",
    # Base
    "InfrastructureError",
    "MessagingError",
    "StorageError",
    # System
    "TelemetryError",
    # Security
    "TokenStoreError",
    "TokenValidationError",
]
