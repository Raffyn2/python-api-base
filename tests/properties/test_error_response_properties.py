"""Property-based tests for error response format.

**Feature: test-coverage-80-percent, Property 7: Error Response Format Consistency**
**Validates: Requirements 6.3**
"""

import pytest
from hypothesis import given, settings, strategies as st

from core.errors import (
    AppError,
    EntityNotFoundError,
    ErrorContext,
    RateLimitExceededError,
    ValidationError,
)


error_message_strategy = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))
)
error_code_strategy = st.from_regex(r"^[A-Z][A-Z0-9_]{2,20}$", fullmatch=True)
status_code_strategy = st.sampled_from([400, 401, 403, 404, 409, 422, 429, 500])


class TestErrorResponseFormatProperties:
    """Property-based tests for error response format consistency."""

    @given(
        message=error_message_strategy,
        error_code=error_code_strategy,
        status_code=status_code_strategy,
    )
    @settings(max_examples=50)
    def test_app_error_to_dict_has_required_fields(
        self, message: str, error_code: str, status_code: int
    ) -> None:
        """
        **Feature: test-coverage-80-percent, Property 7: Error Response Format**

        For any AppError, to_dict() SHALL contain all required fields.
        """
        error = AppError(
            message=message,
            error_code=error_code,
            status_code=status_code,
        )
        result = error.to_dict()

        assert "message" in result
        assert "error_code" in result
        assert "status_code" in result
        assert "correlation_id" in result
        assert "timestamp" in result

    @given(
        entity_type=st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll"),
        )).filter(lambda s: s.strip()),
        entity_id=st.text(min_size=1, max_size=36, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
        )).filter(lambda s: s.strip()),
    )
    @settings(max_examples=50)
    def test_entity_not_found_error_format(
        self, entity_type: str, entity_id: str
    ) -> None:
        """
        **Feature: test-coverage-80-percent, Property 7: Error Response Format**

        For any EntityNotFoundError, response SHALL include entity info.
        """
        error = EntityNotFoundError(entity_type=entity_type, entity_id=entity_id)
        result = error.to_dict()

        assert result["status_code"] == 404
        assert result["details"]["entity_type"] == entity_type
        assert result["details"]["entity_id"] == entity_id

    @given(retry_after=st.integers(min_value=1, max_value=3600))
    @settings(max_examples=50)
    def test_rate_limit_error_format(self, retry_after: int) -> None:
        """
        **Feature: test-coverage-80-percent, Property 7: Error Response Format**

        For any RateLimitExceededError, response SHALL include retry_after.
        """
        error = RateLimitExceededError(retry_after=retry_after)
        result = error.to_dict()

        assert result["status_code"] == 429
        assert result["details"]["retry_after"] == retry_after


class TestErrorContextProperties:
    """Property-based tests for ErrorContext."""

    @given(
        path_segments=st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="_-"
            )),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=50)
    def test_error_context_preserves_path(self, path_segments: list) -> None:
        """
        **Feature: test-coverage-80-percent, Property 7: Error Response Format**

        For any ErrorContext, request_path SHALL be preserved in to_dict().
        """
        request_path = "/" + "/".join(path_segments)
        ctx = ErrorContext(request_path=request_path)
        result = ctx.to_dict()

        assert result["request_path"] == request_path
