"""RFC 7807 Problem Details response DTO.

Re-exports ProblemDetail from core.errors.http for backward compatibility.
The canonical implementation is in core/errors/http/problem_details.py.

**Feature: application-layer-improvements-2025**
**Refactored: 2025 - Consolidated to core.errors.http (Single Source of Truth)**
"""

# Re-export from canonical location (Single Source of Truth)
from core.errors.http.problem_details import (
    PROBLEM_JSON_MEDIA_TYPE,
    ProblemDetail,
    ValidationErrorDetail,
)

__all__ = [
    "PROBLEM_JSON_MEDIA_TYPE",
    "ProblemDetail",
    "ValidationErrorDetail",
]
