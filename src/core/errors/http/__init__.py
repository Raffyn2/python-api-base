"""HTTP/API error handling.

- Problem Details: RFC 7807 compliant responses
- Exception Handlers: FastAPI exception handlers
- Constants: HTTP status codes and error codes
"""

from core.errors.http.constants import (
    ErrorCode,
    ErrorCodes,
    ErrorMessages,
    HttpStatus,
)
from core.errors.http.exception_handlers import (
    generic_exception_handler,
    http_exception_handler,
    setup_exception_handlers,
    validation_exception_handler,
)
from core.errors.http.problem_details import (
    PROBLEM_JSON_MEDIA_TYPE,
    ProblemDetail,
    ValidationErrorDetail,
)

__all__ = [
    # Problem Details
    "ProblemDetail",
    "ValidationErrorDetail",
    "PROBLEM_JSON_MEDIA_TYPE",
    # Exception Handlers
    "setup_exception_handlers",
    "http_exception_handler",
    "validation_exception_handler",
    "generic_exception_handler",
    # Constants
    "HttpStatus",
    "ErrorCode",
    "ErrorCodes",
    "ErrorMessages",
]
