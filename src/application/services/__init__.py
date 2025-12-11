"""Cross-cutting application services.

Provides shared services used across bounded contexts:
- Feature Flags: Controlled feature rollouts
- File Upload: S3-compatible file handling
- Multitenancy: Tenant isolation

**Architecture: Cross-Cutting Concerns**
"""

from application.services.feature_flags import (
    FeatureFlagService,
    FlagConfig,
    FlagStatus,
)
from application.services.file_upload import (
    FileMetadata,
    FileUploadService,
    UploadResult,
)
from application.services.multitenancy import (
    TenantContext,
    TenantMiddleware,
    get_current_tenant,
)

__all__ = [
    # Feature Flags
    "FeatureFlagService",
    # File Upload
    "FileMetadata",
    "FileUploadService",
    "FlagConfig",
    "FlagStatus",
    # Multitenancy
    "TenantContext",
    "TenantMiddleware",
    "UploadResult",
    "get_current_tenant",
]
