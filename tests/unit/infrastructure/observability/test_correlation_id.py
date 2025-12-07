"""Unit tests for correlation ID module.

Tests correlation ID generation, context management, and propagation.
"""

import pytest

from infrastructure.observability.correlation_id import (
    CorrelationConfig,
    CorrelationContext,
    CorrelationContextManager,
    CorrelationService,
    IdFormat,
    clear_context,
    generate_id,
    get_correlation_id,
    get_current_context,
    get_request_id,
    get_span_id,
    set_correlation_id,
    set_request_id,
)


class TestIdFormat:
    """Tests for IdFormat enum."""

    def test_uuid4_value(self) -> None:
        """Test UUID4 format value."""
        assert IdFormat.UUID4.value == "uuid4"

    def test_uuid4_hex_value(self) -> None:
        """Test UUID4_HEX format value."""
        assert IdFormat.UUID4_HEX.value == "uuid4_hex"

    def test_short_value(self) -> None:
        """Test SHORT format value."""
        assert IdFormat.SHORT.value == "short"

    def test_timestamp_value(self) -> None:
        """Test TIMESTAMP format value."""
        assert IdFormat.TIMESTAMP.value == "timestamp"


class TestGenerateId:
    """Tests for generate_id function."""

    def test_uuid4_format(self) -> None:
        """Test UUID4 format generation."""
        id_value = generate_id(IdFormat.UUID4)
        assert len(id_value) == 36  # UUID with dashes
        assert "-" in id_value

    def test_uuid4_hex_format(self) -> None:
        """Test UUID4_HEX format generation."""
        id_value = generate_id(IdFormat.UUID4_HEX)
        assert len(id_value) == 32
        assert "-" not in id_value

    def test_short_format(self) -> None:
        """Test SHORT format generation."""
        id_value = generate_id(IdFormat.SHORT)
        assert len(id_value) == 16

    def test_timestamp_format(self) -> None:
        """Test TIMESTAMP format generation."""
        id_value = generate_id(IdFormat.TIMESTAMP)
        assert "-" in id_value
        # Format: YYYYMMDDHHMMSS-xxxxxxxxxxxx
        parts = id_value.split("-")
        assert len(parts) == 2
        assert len(parts[0]) == 14  # Timestamp part

    def test_uniqueness(self) -> None:
        """Test generated IDs are unique."""
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100


class TestContextVars:
    """Tests for context variable functions."""

    def setup_method(self) -> None:
        """Clear context before each test."""
        clear_context()

    def teardown_method(self) -> None:
        """Clear context after each test."""
        clear_context()

    def test_set_and_get_correlation_id(self) -> None:
        """Test setting and getting correlation ID."""
        set_correlation_id("corr-123")
        assert get_correlation_id() == "corr-123"

    def test_set_and_get_request_id(self) -> None:
        """Test setting and getting request ID."""
        set_request_id("req-456")
        assert get_request_id() == "req-456"

    def test_default_values_are_none(self) -> None:
        """Test default context values are None."""
        assert get_correlation_id() is None
        assert get_request_id() is None
        assert get_span_id() is None

    def test_clear_context(self) -> None:
        """Test clearing context."""
        set_correlation_id("corr-1")
        set_request_id("req-1")
        clear_context()
        assert get_correlation_id() is None
        assert get_request_id() is None


class TestCorrelationContext:
    """Tests for CorrelationContext dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic context creation."""
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        assert ctx.correlation_id == "corr-123"
        assert ctx.request_id == "req-456"
        assert ctx.span_id is None

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
            span_id="span-789",
        )
        result = ctx.to_dict()
        assert result["correlation_id"] == "corr-123"
        assert result["request_id"] == "req-456"
        assert result["span_id"] == "span-789"

    def test_to_dict_excludes_none(self) -> None:
        """Test to_dict excludes None values."""
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        result = ctx.to_dict()
        assert "span_id" not in result
        assert "parent_span_id" not in result

    def test_to_headers(self) -> None:
        """Test conversion to HTTP headers."""
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        headers = ctx.to_headers()
        assert headers["X-Correlation-ID"] == "corr-123"
        assert headers["X-Request-ID"] == "req-456"

    def test_from_headers(self) -> None:
        """Test creation from HTTP headers."""
        headers = {
            "X-Correlation-ID": "corr-from-header",
            "X-Request-ID": "req-from-header",
        }
        ctx = CorrelationContext.from_headers(headers)
        assert ctx.correlation_id == "corr-from-header"
        assert ctx.request_id == "req-from-header"

    def test_from_headers_generates_missing(self) -> None:
        """Test from_headers generates missing IDs."""
        ctx = CorrelationContext.from_headers({}, generate_missing=True)
        assert ctx.correlation_id != ""
        assert ctx.request_id != ""

    def test_create_new(self) -> None:
        """Test creating new context."""
        ctx = CorrelationContext.create_new(service_name="test-service")
        assert ctx.correlation_id != ""
        assert ctx.request_id != ""
        assert ctx.span_id is not None
        assert ctx.service_name == "test-service"


class TestCorrelationContextManager:
    """Tests for CorrelationContextManager."""

    def setup_method(self) -> None:
        """Clear context before each test."""
        clear_context()

    def teardown_method(self) -> None:
        """Clear context after each test."""
        clear_context()

    def test_context_manager_sets_values(self) -> None:
        """Test context manager sets correlation values."""
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        with CorrelationContextManager(ctx):
            assert get_correlation_id() == "corr-123"
            assert get_request_id() == "req-456"

    def test_context_manager_restores_values(self) -> None:
        """Test context manager restores previous values."""
        set_correlation_id("original-corr")
        ctx = CorrelationContext(
            correlation_id="new-corr",
            request_id="new-req",
        )
        with CorrelationContextManager(ctx):
            assert get_correlation_id() == "new-corr"
        # After exit, original value should be restored
        assert get_correlation_id() == "original-corr"

    def test_context_manager_returns_context(self) -> None:
        """Test context manager returns context object."""
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        with CorrelationContextManager(ctx) as returned_ctx:
            assert returned_ctx.correlation_id == "corr-123"

    def test_context_manager_creates_new_if_none(self) -> None:
        """Test context manager creates new context if none provided."""
        with CorrelationContextManager() as ctx:
            assert ctx.correlation_id != ""
            assert ctx.request_id != ""


class TestGetCurrentContext:
    """Tests for get_current_context function."""

    def setup_method(self) -> None:
        """Clear context before each test."""
        clear_context()

    def teardown_method(self) -> None:
        """Clear context after each test."""
        clear_context()

    def test_returns_none_when_empty(self) -> None:
        """Test returns None when no context set."""
        assert get_current_context() is None

    def test_returns_context_when_set(self) -> None:
        """Test returns context when values are set."""
        set_correlation_id("corr-123")
        set_request_id("req-456")
        ctx = get_current_context()
        assert ctx is not None
        assert ctx.correlation_id == "corr-123"
        assert ctx.request_id == "req-456"


class TestCorrelationConfig:
    """Tests for CorrelationConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CorrelationConfig()
        assert config.header_name == "X-Correlation-ID"
        assert config.request_id_header == "X-Request-ID"
        assert config.generate_if_missing is True
        assert config.id_format == IdFormat.UUID4_HEX
        assert config.propagate_to_response is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = CorrelationConfig(
            header_name="X-Custom-Correlation",
            generate_if_missing=False,
            id_format=IdFormat.SHORT,
            service_name="my-service",
        )
        assert config.header_name == "X-Custom-Correlation"
        assert config.generate_if_missing is False
        assert config.id_format == IdFormat.SHORT
        assert config.service_name == "my-service"


class TestCorrelationService:
    """Tests for CorrelationService."""

    def test_create_context(self) -> None:
        """Test creating new context."""
        service = CorrelationService()
        ctx = service.create_context()
        assert ctx.correlation_id != ""
        assert ctx.request_id != ""

    def test_extract_from_headers(self) -> None:
        """Test extracting context from headers."""
        service = CorrelationService()
        headers = {
            "X-Correlation-ID": "corr-from-header",
            "X-Request-ID": "req-from-header",
        }
        ctx = service.extract_from_headers(headers)
        assert ctx.correlation_id == "corr-from-header"
        assert ctx.request_id == "req-from-header"

    def test_get_response_headers(self) -> None:
        """Test getting response headers."""
        service = CorrelationService()
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        headers = service.get_response_headers(ctx)
        assert headers["X-Correlation-ID"] == "corr-123"

    def test_get_response_headers_disabled(self) -> None:
        """Test response headers disabled."""
        config = CorrelationConfig(propagate_to_response=False)
        service = CorrelationService(config)
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        headers = service.get_response_headers(ctx)
        assert headers == {}

    def test_bind_context(self) -> None:
        """Test binding context."""
        service = CorrelationService()
        ctx = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        manager = service.bind_context(ctx)
        assert isinstance(manager, CorrelationContextManager)
