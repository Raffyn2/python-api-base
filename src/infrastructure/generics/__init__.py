"""Generic infrastructure protocols and utilities.

**Feature: infrastructure-generics-review-2025**
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 3.1, 4.1**

This module provides:
- Generic protocols for Repository, Service, Factory, Store patterns
- Centralized error messages and typed error classes
- Standardized status enums for all infrastructure modules
- Shared validation utilities and configuration patterns
"""

from .config import (
    BaseConfig,
    ConfigBuilder,
)
from .errors import (
    AuthenticationError,
    CacheError,
    ErrorMessages,
    InfrastructureError,
    MessagingError,
    PoolError,
    SecurityError,
    ValidationError,
)
from .protocols import (
    AsyncRepository,
    AsyncService,
    Factory,
    Repository,
    Service,
    Store,
)
from .status import (
    BaseStatus,
    CacheStatus,
    ConnectionStatus,
    HealthStatus,
    TaskStatus,
)
from .validators import (
    ValidationResult,
    validate_format,
    validate_non_empty,
    validate_range,
    validate_required,
)

__all__ = [
    # Protocols
    "Repository",
    "Service",
    "Factory",
    "Store",
    "AsyncRepository",
    "AsyncService",
    # Errors
    "ErrorMessages",
    "InfrastructureError",
    "AuthenticationError",
    "CacheError",
    "PoolError",
    "ValidationError",
    "SecurityError",
    "MessagingError",
    # Status Enums
    "BaseStatus",
    "ConnectionStatus",
    "TaskStatus",
    "HealthStatus",
    "CacheStatus",
    # Validators
    "validate_non_empty",
    "validate_range",
    "validate_format",
    "validate_required",
    "ValidationResult",
    # Config
    "BaseConfig",
    "ConfigBuilder",
]
