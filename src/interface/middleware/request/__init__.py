"""Request processing middleware.

**Feature: api-architecture-analysis**
**Validates: Requirements 4.4, 6.4**
"""

from interface.middleware.request.request_id import (
    RequestIDMiddleware,
    get_request_id,
)
from interface.middleware.request.request_size_limit import (
    RequestSizeLimitMiddleware,
    RouteSizeLimit,
    StreamingRequestSizeLimitMiddleware,
    create_size_limit_middleware,
)
from interface.middleware.request.timeout import (
    TimeoutAction,
    TimeoutConfig,
    TimeoutConfigBuilder,
    TimeoutError,
    TimeoutMiddleware,
    TimeoutResult,
    create_timeout_middleware,
    timeout_decorator,
)

__all__ = [
    # Request ID
    "RequestIDMiddleware",
    # Request Size Limit
    "RequestSizeLimitMiddleware",
    "RouteSizeLimit",
    "StreamingRequestSizeLimitMiddleware",
    # Timeout
    "TimeoutAction",
    "TimeoutConfig",
    "TimeoutConfigBuilder",
    "TimeoutError",
    "TimeoutMiddleware",
    "TimeoutResult",
    "create_size_limit_middleware",
    "create_timeout_middleware",
    "get_request_id",
    "timeout_decorator",
]
