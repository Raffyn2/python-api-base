"""Generic infrastructure protocols and utilities.

**Feature: infrastructure-generics-review-2025**
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 3.1, 4.1**

This module provides:
- Generic protocols for Repository, Service, Factory, Store patterns
- Centralized error messages and typed error classes
- Standardized status enums for all infrastructure modules
- Shared validation utilities and configuration patterns
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
    BaseStatus,
    CacheStatus,
    ConnectionStatus,
    HealthStatus,
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
    "AuthenticationError",
    # Config
    "BaseConfig",
    # Status Enums
    "BaseStatus",
    "CacheError",
    "CacheStatus",
    "ConfigBuilder",
    "ConnectionStatus",
    # Errors
    "ErrorMessages",
    "Factory",
    "HealthStatus",
    "InfrastructureError",
    "MessagingError",
    "PoolError",
    # Protocols
    "Repository",
    "SecurityError",
    "Service",
    "Store",
    "TaskStatus",
    "ValidationError",
    "ValidationResult",
    "validate_format",
    # Validators
    "validate_non_empty",
    "validate_range",
    "validate_required",
]
