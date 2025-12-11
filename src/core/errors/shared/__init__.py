"""Shared module exceptions.

**Feature: shared-modules-refactoring**
"""

from core.errors.shared.exceptions import (
    AuthenticationError,
    BanOperationError,
    DecryptionError,
    EncryptionError,
    EntityResolutionError,
    FederationValidationError,
    FilterValidationError,
    LockAcquisitionTimeoutError,
    PatternValidationError,
    Phase2ModuleError,
    PoolInvariantViolationError,
    RollbackError,
    SecurityModuleError,
    SharedModuleError,
    SnapshotIntegrityError,
    TaskExecutionError,
    ValidationError,
)
from core.errors.shared.generic_errors import (
    ApplicationError as GenericApplicationError,
    DomainError as GenericDomainError,
    ErrorContext as GenericErrorContext,
    InfrastructureError as GenericInfrastructureError,
    map_error,
)

__all__ = [
    "AuthenticationError",
    "BanOperationError",
    "DecryptionError",
    "EncryptionError",
    "EntityResolutionError",
    "FederationValidationError",
    "FilterValidationError",
    # Generic errors with PEP 695 type parameters
    "GenericApplicationError",
    "GenericDomainError",
    "GenericErrorContext",
    "GenericInfrastructureError",
    "LockAcquisitionTimeoutError",
    "PatternValidationError",
    "Phase2ModuleError",
    "PoolInvariantViolationError",
    "RollbackError",
    "SecurityModuleError",
    "SharedModuleError",
    "SnapshotIntegrityError",
    "TaskExecutionError",
    "ValidationError",
    "map_error",
]
