"""Unit tests for correlation ID module.

Tests IdFormat, generate_id, CorrelationContext, CorrelationContextManager,
CorrelationConfig, and CorrelationService.
"""

from datetime import UTC, datetime

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
    get_request_id,
    get_span_id,
    set_correlation_id,
    set_request_id,
)


class TestIdFormat:
    """Tests for IdFormat enum."""

    def test_uuid4_value(self) -> None:
        """Test UUID4 value."""
        assert IdFormat.UUID4.value == "uuid4"

    def test_uuid4_hex_value(self) -> None:
        """Test UUID4_HEX value."""
        assert IdFormat.UUID4_HEX.value == "uuid4_hex"

    def test_short_value(self) -> None:
        """Test SHORT value."""
        assert IdFormat.SHORT.value == "short"

    def test_timestamp_value(self) -> None:
        """Test TIMESTAMP value."""
        assert IdFormat.TIMESTAMP.value == "timestamp"


class TestGenerateId:
    """Tests for generate_id function."""

    def test_uuid4_format(self) -> None:
        """Test UUID4 format includes dashes."""
        result = generate_id(IdFormat.UUID4)
        
        assert "-" in result
        assert len(result) == 36

    def test_uuid4_hex_format(self) -> None:
        """Test UUID4_HEX format is 32 chars."""
        result = generate_id(IdFormat.UUID4_HEX)
        
        assert "-" not in result
        assert len(result) == 32

    def test_short_format(self) -> None:
        """Test SHORT format is 16 chars."""
        result = generate_id(IdFormat.SHORT)
        
        assert len(result) == 16

    def test_timestamp_format(self) -> None:
        """Test TIMESTAMP format includes timestamp."""
        result = generate_id(IdFormat.TIMESTAMP)
        
        assert "-" in result
        # Should start with date pattern
        assert result[:4].isdigit()

    def test_uniqueness(self) -> None:
        """Test generated IDs are unique."""
        ids = [generate_id() for _ in range(100)]
        
        assert len(set(ids)) == 100


class TestContextVars:
    """Tests for context variable functions."""

    def setup_method(self) -> None:
        """Clear context before each test."""
        clear_context()

    def teardown_method(self) -> None:
        """Clear context after each test."""
        clear_context()

    def test_set_get_correlation_id(self) -> None:
        """Test setting and getting correlation ID."""
        set_correlation_id("test-correlation-id")
        
        result = get_correlation_id()
        
        assert result == "test-correlation-id"

    def test_set_get_request_id(self) -> None:
        """Test setting and getting request ID."""
        set_request_id("test-request-id")
        
        result = get_request_id()
        
        assert result == "test-request-id"

    def test_get_correlation_id_none(self) -> None:
        """Test getting correlation ID when not set."""
        result = get_correlation_id()
        
        assert result is None

    def test_clear_context(self) -> None:
        """Test clearing all context."""
        set_correlation_id("test")
        set_request_id("test")
        
        clear_context()
        
        assert get_correlation_id() is None
        assert get_request_id() is None


class TestCorrelationContext:
    """Tests for CorrelationContext dataclass."""

    def test_creation(self) -> None:
        """Test CorrelationContext creation."""
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        
        assert context.correlation_id == "corr-123"
        assert context.request_id == "req-456"
        assert context.span_id is None
        assert context.parent_span_id is None

    def test_creation_with_all_fields(self) -> None:
        """Test CorrelationContext with all fields."""
        now = datetime.now(UTC)
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
            span_id="span-789",
            parent_span_id="parent-000",
            trace_id="trace-111",
            service_name="test-service",
            timestamp=now,
        )
        
        assert context.span_id == "span-789"
        assert context.parent_span_id == "parent-000"
        assert context.trace_id == "trace-111"
        assert context.service_name == "test-service"
        assert context.timestamp == now

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
            span_id="span-789",
        )
        
        result = context.to_dict()
        
        assert result["correlation_id"] == "corr-123"
        assert result["request_id"] == "req-456"
        assert result["span_id"] == "span-789"

    def test_to_headers(self) -> None:
        """Test to_headers conversion."""
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        
        result = context.to_headers()
        
        assert result["X-Correlation-ID"] == "corr-123"
        assert result["X-Request-ID"] == "req-456"

    def test_from_headers(self) -> None:
        """Test from_headers creation."""
        headers = {
            "X-Correlation-ID": "corr-123",
            "X-Request-ID": "req-456",
        }
        
        context = CorrelationContext.from_headers(headers)
        
        assert context.correlation_id == "corr-123"
        assert context.request_id == "req-456"

    def test_from_headers_generate_missing(self) -> None:
        """Test from_headers generates missing IDs."""
        headers = {}
        
        context = CorrelationContext.from_headers(headers, generate_missing=True)
        
        assert context.correlation_id != ""
        assert context.request_id != ""

    def test_create_new(self) -> None:
        """Test create_new factory."""
        context = CorrelationContext.create_new(service_name="test-service")
        
        assert context.correlation_id != ""
        assert context.request_id != ""
        assert context.span_id is not None
        assert context.service_name == "test-service"


class TestCorrelationContextManager:
    """Tests for CorrelationContextManager."""

    def setup_method(self) -> None:
        """Clear context before each test."""
        clear_context()

    def teardown_method(self) -> None:
        """Clear context after each test."""
        clear_context()

    def test_context_manager(self) -> None:
        """Test context manager sets and clears context."""
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        
        with CorrelationContextManager(context) as ctx:
            assert get_correlation_id() == "corr-123"
            assert get_request_id() == "req-456"
            assert ctx.correlation_id == "corr-123"

    def test_context_manager_with_span(self) -> None:
        """Test context manager with span ID."""
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
            span_id="span-789",
        )
        
        with CorrelationContextManager(context):
            assert get_span_id() == "span-789"


class TestCorrelationConfig:
    """Tests for CorrelationConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CorrelationConfig()
        
        assert config.header_name == "X-Correlation-ID"
        assert config.request_id_header == "X-Request-ID"
        assert config.generate_if_missing is True
        assert config.id_format == IdFormat.UUID4_HEX
        assert config.propagate_to_response is True
        assert config.service_name is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = CorrelationConfig(
            header_name="X-Custom-Correlation",
            request_id_header="X-Custom-Request",
            generate_if_missing=False,
            id_format=IdFormat.UUID4,
            propagate_to_response=False,
            service_name="my-service",
        )
        
        assert config.header_name == "X-Custom-Correlation"
        assert config.service_name == "my-service"


class TestCorrelationService:
    """Tests for CorrelationService."""

    def test_extract_from_headers(self) -> None:
        """Test extracting context from headers."""
        service = CorrelationService()
        headers = {
            "X-Correlation-ID": "corr-123",
            "X-Request-ID": "req-456",
        }
        
        context = service.extract_from_headers(headers)
        
        assert context.correlation_id == "corr-123"
        assert context.request_id == "req-456"

    def test_create_context(self) -> None:
        """Test creating new context."""
        config = CorrelationConfig(service_name="test-service")
        service = CorrelationService(config)
        
        context = service.create_context()
        
        assert context.correlation_id != ""
        assert context.service_name == "test-service"

    def test_get_response_headers(self) -> None:
        """Test getting response headers."""
        service = CorrelationService()
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        
        headers = service.get_response_headers(context)
        
        assert headers["X-Correlation-ID"] == "corr-123"

    def test_get_response_headers_disabled(self) -> None:
        """Test response headers when propagation disabled."""
        config = CorrelationConfig(propagate_to_response=False)
        service = CorrelationService(config)
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        
        headers = service.get_response_headers(context)
        
        assert headers == {}

    def test_bind_context(self) -> None:
        """Test binding context."""
        service = CorrelationService()
        context = CorrelationContext(
            correlation_id="corr-123",
            request_id="req-456",
        )
        
        manager = service.bind_context(context)
        
        assert isinstance(manager, CorrelationContextManager)
