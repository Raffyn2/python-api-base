"""Logging and error handling middleware.

**Feature: api-base-improvements**
**Validates: Requirements 9.1, 9.2, 9.3, 9.5**
"""

from interface.middleware.logging.error_handler import (
    app_exception_handler,
    create_problem_detail,
    register_exception_handlers,
    unhandled_exception_handler,
    validation_exception_handler,
)
from interface.middleware.logging.request_logger import (
    MASK_VALUE,
    SENSITIVE_FIELDS,
    SENSITIVE_HEADERS,
    RequestLogEntry,
    RequestLoggerMiddleware,
    ResponseLogEntry,
    mask_dict,
    mask_sensitive_value,
    sanitize_headers,
)

__all__ = [
    # Request logger
    "MASK_VALUE",
    "SENSITIVE_FIELDS",
    "SENSITIVE_HEADERS",
    "RequestLogEntry",
    "RequestLoggerMiddleware",
    "ResponseLogEntry",
    # Error handlers
    "app_exception_handler",
    "create_problem_detail",
    "mask_dict",
    "mask_sensitive_value",
    "register_exception_handlers",
    "sanitize_headers",
    "unhandled_exception_handler",
    "validation_exception_handler",
]
