"""Property-based tests for error serialization.

Tests error serialization consistency using Hypothesis.

**Property 3: Exception Serialization Consistency**
**Requirements: 2.2**
"""

from hypothesis import given, settings, strategies as st

from core.errors.base.domain_errors import (
    AppError,
    EntityNotFoundError,
    ErrorContext,
    RateLimitExceededError,
    ValidationError,
)


class TestErrorContextProperties:
    """Property tests for ErrorContext."""

    @given(
        correlation_id=st.text(min_size=1, max_size=50).filter(str.strip),
        request_path=st.text(min_size=1, max_size=100).filter(str.strip),
    )
    @settings(max_examples=100)
    def test_to_dict_preserves_values(self, correlation_id: str, request_path: str) -> None:
        """Property: to_dict preserves all context values."""
        ctx = ErrorContext(
            correlation_id=correlation_id,
            request_path=request_path,
        )
        result = ctx.to_dict()

        assert result["correlation_id"] == correlation_id
        assert result["request_path"] == request_path
        assert "timestamp" in result


class TestAppErrorProperties:
    """Property tests for AppError serialization."""

    @given(
        message=st.text(min_size=1, max_size=200).filter(str.strip),
        error_code=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=50,
        ).filter(str.strip),
        status_code=st.integers(min_value=400, max_value=599),
    )
    @settings(max_examples=100)
    def test_to_dict_contains_all_fields(self, message: str, error_code: str, status_code: int) -> None:
        """Property: to_dict contains all required fields."""
        error = AppError(
            message=message,
            error_code=error_code,
            status_code=status_code,
        )
        result = error.to_dict()

        assert result["message"] == message
        assert result["error_code"] == error_code
        assert result["status_code"] == status_code
        assert "correlation_id" in result
        assert "timestamp" in result
        assert "details" in result

    @given(
        key=st.text(min_size=1, max_size=20).filter(str.isalnum),
        value=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=50)
    def test_details_preserved_in_serialization(self, key: str, value: str) -> None:
        """Property: Details are preserved in serialization."""
        error = AppError(
            message="Test",
            error_code="TEST",
            details={key: value},
        )
        result = error.to_dict()

        assert result["details"][key] == value


class TestEntityNotFoundErrorProperties:
    """Property tests for EntityNotFoundError."""

    @given(
        entity_type=st.text(min_size=1, max_size=50).filter(str.isalnum),
        entity_id=st.text(min_size=1, max_size=50).filter(str.strip),
    )
    @settings(max_examples=100)
    def test_message_contains_entity_info(self, entity_type: str, entity_id: str) -> None:
        """Property: Message contains entity type and ID."""
        error = EntityNotFoundError(entity_type=entity_type, entity_id=entity_id)

        assert entity_type in error.message
        assert entity_id in error.message
        assert error.status_code == 404


class TestValidationErrorProperties:
    """Property tests for ValidationError."""

    @given(
        field=st.text(min_size=1, max_size=30).filter(str.isalnum),
        message=st.text(min_size=1, max_size=100).filter(str.strip),
    )
    @settings(max_examples=100)
    def test_dict_errors_normalized_to_list(self, field: str, message: str) -> None:
        """Property: Dict errors are normalized to list format."""
        error = ValidationError(errors={field: message})
        result = error.to_dict()

        errors_list = result["details"]["errors"]
        assert isinstance(errors_list, list)
        assert any(e["field"] == field for e in errors_list)


class TestRateLimitExceededErrorProperties:
    """Property tests for RateLimitExceededError."""

    @given(retry_after=st.integers(min_value=1, max_value=86400))
    @settings(max_examples=100)
    def test_retry_after_in_details(self, retry_after: int) -> None:
        """Property: retry_after is always in details."""
        error = RateLimitExceededError(retry_after=retry_after)
        result = error.to_dict()

        assert result["details"]["retry_after"] == retry_after
        assert error.status_code == 429
