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
    app_error_handler,
    generic_exception_handler,
    http_exception_handler,
    pydantic_exception_handler,
    setup_exception_handlers,
    validation_exception_handler,
)
from core.errors.http.problem_details import (
    PROBLEM_JSON_MEDIA_TYPE,
    ProblemDetail,
    ValidationErrorDetail,
)

__all__ = [
    "PROBLEM_JSON_MEDIA_TYPE",
    "ErrorCode",
    "ErrorCodes",
    "ErrorMessages",
    # Constants
    "HttpStatus",
    # Problem Details
    "ProblemDetail",
    "ValidationErrorDetail",
    # Exception Handlers
    "app_error_handler",
    "generic_exception_handler",
    "http_exception_handler",
    "pydantic_exception_handler",
    "setup_exception_handlers",
    "validation_exception_handler",
]
