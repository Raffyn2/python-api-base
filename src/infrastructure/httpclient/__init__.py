"""Generic HTTP client infrastructure with PEP 695 type parameters.

**Feature: enterprise-generics-2025**
**Requirement: R9 - Generic HTTP Client with Resilience**
**Improvement: P1-1 - Added JSON type definitions for better type safety**

Exports:
    - HttpClient[TRequest, TResponse]: Generic HTTP client
    - HttpClientConfig: Configuration
    - HttpError: Base error class
    - TimeoutError: Timeout error
    - ValidationError: Response validation error
    - CircuitBreakerError: Circuit breaker error
    - RetryPolicy: Retry policy configuration
    - CircuitState: Circuit breaker states
    - JsonObject, JsonValue, JsonPrimitive, JsonArray: JSON type definitions
"""

from infrastructure.httpclient.client import HttpClient
from infrastructure.httpclient.errors import (
    CircuitBreakerError,
    HttpError,
    TimeoutError,
    ValidationError,
)
from infrastructure.httpclient.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    HttpClientConfig,
    RetryPolicy,
)
from infrastructure.httpclient.types import (
    JsonArray,
    JsonObject,
    JsonPrimitive,
    JsonValue,
)

__all__ = [
    # Resilience
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitState",
    # Client
    "HttpClient",
    # Configuration
    "HttpClientConfig",
    # Errors
    "HttpError",
    "JsonArray",
    # Types
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
    "RetryPolicy",
    "TimeoutError",
    "ValidationError",
]
