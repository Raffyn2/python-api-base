"""Idempotency error types.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 23.4**
"""


class IdempotencyKeyConflictError(Exception):
    """Raised when idempotency key is reused with different request body.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.4**
    """

    def __init__(self, idempotency_key: str) -> None:
        self.idempotency_key = idempotency_key
        super().__init__(
            f"Idempotency key '{idempotency_key}' was already used with a different request body"
        )


class IdempotencyKeyMissingError(Exception):
    """Raised when idempotency key is required but not provided.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 23.5**
    """

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        super().__init__(
            f"Idempotency-Key header is required for endpoint: {endpoint}"
        )
