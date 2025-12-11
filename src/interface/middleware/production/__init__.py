"""Production-ready middleware using generic infrastructure components.

Re-exports all middleware classes for backward compatibility.
Implementation split into focused modules for one-class-per-file compliance.

**Feature: python-api-base-2025-generics-audit**
**Validates: Requirements 13, 16, 18, 19, 22**
**Refactored: Split into focused modules for one-class-per-file compliance**
"""

# Re-export all classes for backward compatibility
from interface.middleware.production.audit import AuditConfig, AuditMiddleware
from interface.middleware.production.feature_flags import (
    FeatureFlagMiddleware,
    is_feature_enabled,
)
from interface.middleware.production.multitenancy import (
    MultitenancyConfig,
    MultitenancyMiddleware,
)
from interface.middleware.production.resilience import (
    ResilienceConfig,
    ResilienceMiddleware,
)
from interface.middleware.production.setup import setup_production_middleware

__all__ = [
    # Audit
    "AuditConfig",
    "AuditMiddleware",
    # Feature Flags
    "FeatureFlagMiddleware",
    # Multitenancy
    "MultitenancyConfig",
    "MultitenancyMiddleware",
    # Resilience
    "ResilienceConfig",
    "ResilienceMiddleware",
    "is_feature_enabled",
    # Setup
    "setup_production_middleware",
]
