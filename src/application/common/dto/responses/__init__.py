"""Response DTOs for API communication.

Provides standard response wrappers for API responses including generic responses,
paginated responses, and RFC 7807 error responses.

**Feature: application-layer-improvements-2025**
**Refactored: 2025 - ProblemDetail consolidated to core.errors.http**
"""

from application.common.dto.responses.api_response import ApiResponse
from application.common.dto.responses.paginated_response import PaginatedResponse
from application.common.dto.responses.problem_detail import (
    PROBLEM_JSON_MEDIA_TYPE,
    ProblemDetail,
    ValidationErrorDetail,
)

__all__ = [
    "PROBLEM_JSON_MEDIA_TYPE",
    "ApiResponse",
    "PaginatedResponse",
    "ProblemDetail",
    "ValidationErrorDetail",
]
