"""Generic infrastructure components.

Contains configuration, error handling, protocols, status, and validators.

**Feature: infrastructure-restructuring-2025**
"""

from infrastructure.generics.core.config import BaseConfig, ConfigBuilder
from infrastructure.generics.core.errors import (
    AuthenticationError,
    CacheError,
    ErrorMessages,
    InfrastructureError,
    MessagingError,
    PoolError,
    SecurityError,
    ValidationError,
)
from infrastructure.generics.core.protocols import (
    AsyncRepository,
    AsyncService,
    Factory,
    Repository,
    Service,
    Store,
)
from infrastructure.generics.core.status import (
    AuthStatus,
    BaseStatus,
    CacheStatus,
    ConnectionStatus,
    HealthStatus,
    MessageStatus,
    TaskStatus,
)
from infrastructure.generics.core.validators import (
    ValidationResult,
    validate_format,
    validate_non_empty,
    validate_range,
    validate_required,
)

__all__ = [
    "AsyncRepository",
    "AsyncService",
    "AuthStatus",
    "AuthenticationError",
    "BaseConfig",
    "BaseStatus",
    "CacheError",
    "CacheStatus",
    "ConfigBuilder",
    "ConnectionStatus",
    "ErrorMessages",
    "Factory",
    "HealthStatus",
    "InfrastructureError",
    "MessageStatus",
    "MessagingError",
    "PoolError",
    "Repository",
    "SecurityError",
    "Service",
    "Store",
    "TaskStatus",
    "ValidationError",
    "ValidationResult",
    "validate_format",
    "validate_non_empty",
    "validate_range",
    "validate_required",
]
