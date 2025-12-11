"""Tests for no-op telemetry implementations.

**Feature: realistic-test-coverage**
**Validates: Requirements 7.2**
"""

from infrastructure.observability.telemetry.noop import (
    _NoOpCounter,
    _NoOpHistogram,
    _NoOpMeter,
    _NoOpSpan,
    _NoOpTracer,
)


class TestNoOpSpan:
    """Tests for _NoOpSpan."""

    def test_context_manager_enter(self) -> None:
        """Test that span can be used as context manager."""
        span = _NoOpSpan()
        with span as s:
            assert s is span

    def test_context_manager_exit(self) -> None:
        """Test that span exits cleanly."""
        span = _NoOpSpan()
        with span:
            pass  # Should not raise

    def test_set_attribute_does_nothing(self) -> None:
        """Test that set_attribute is a no-op."""
        span = _NoOpSpan()
        span.set_attribute("key", "value")
        span.set_attribute("number", 42)
        span.set_attribute("flag", True)

    def test_add_event_does_nothing(self) -> None:
        """Test that add_event is a no-op."""
        span = _NoOpSpan()
        span.add_event("event_name")
        span.add_event("event_with_attrs", attributes={"key": "value"})

    def test_record_exception_does_nothing(self) -> None:
        """Test that record_exception is a no-op."""
        span = _NoOpSpan()
        span.record_exception(ValueError("test error"))
        span.record_exception(RuntimeError("another error"))

    def test_set_status_does_nothing(self) -> None:
        """Test that set_status is a no-op."""
        span = _NoOpSpan()
        span.set_status("OK")
        span.set_status(0, "Success")
        span.set_status("ERROR", "Something failed")


class TestNoOpTracer:
    """Tests for _NoOpTracer."""

    def test_start_as_current_span_returns_noop_span(self) -> None:
        """Test that start_as_current_span returns a NoOpSpan."""
        tracer = _NoOpTracer()
        span = tracer.start_as_current_span("test_span")
        assert isinstance(span, _NoOpSpan)

    def test_start_as_current_span_with_kwargs(self) -> None:
        """Test start_as_current_span with additional kwargs."""
        tracer = _NoOpTracer()
        span = tracer.start_as_current_span(
            "test_span",
            attributes={"key": "value"},
            kind="internal",
        )
        assert isinstance(span, _NoOpSpan)

    def test_start_span_returns_noop_span(self) -> None:
        """Test that start_span returns a NoOpSpan."""
        tracer = _NoOpTracer()
        span = tracer.start_span("test_span")
        assert isinstance(span, _NoOpSpan)

    def test_start_span_with_kwargs(self) -> None:
        """Test start_span with additional kwargs."""
        tracer = _NoOpTracer()
        span = tracer.start_span(
            "test_span",
            attributes={"key": "value"},
        )
        assert isinstance(span, _NoOpSpan)

    def test_span_can_be_used_as_context_manager(self) -> None:
        """Test that returned span works as context manager."""
        tracer = _NoOpTracer()
        with tracer.start_as_current_span("test") as span:
            span.set_attribute("key", "value")


class TestNoOpMeter:
    """Tests for _NoOpMeter."""

    def test_create_counter_returns_noop_counter(self) -> None:
        """Test that create_counter returns a NoOpCounter."""
        meter = _NoOpMeter()
        counter = meter.create_counter("test_counter")
        assert isinstance(counter, _NoOpCounter)

    def test_create_counter_with_kwargs(self) -> None:
        """Test create_counter with additional kwargs."""
        meter = _NoOpMeter()
        counter = meter.create_counter(
            "test_counter",
            description="A test counter",
            unit="requests",
        )
        assert isinstance(counter, _NoOpCounter)

    def test_create_histogram_returns_noop_histogram(self) -> None:
        """Test that create_histogram returns a NoOpHistogram."""
        meter = _NoOpMeter()
        histogram = meter.create_histogram("test_histogram")
        assert isinstance(histogram, _NoOpHistogram)

    def test_create_histogram_with_kwargs(self) -> None:
        """Test create_histogram with additional kwargs."""
        meter = _NoOpMeter()
        histogram = meter.create_histogram(
            "test_histogram",
            description="A test histogram",
            unit="ms",
        )
        assert isinstance(histogram, _NoOpHistogram)

    def test_create_up_down_counter_returns_noop_counter(self) -> None:
        """Test that create_up_down_counter returns a NoOpCounter."""
        meter = _NoOpMeter()
        counter = meter.create_up_down_counter("test_gauge")
        assert isinstance(counter, _NoOpCounter)


class TestNoOpCounter:
    """Tests for _NoOpCounter."""

    def test_add_with_int(self) -> None:
        """Test add with integer value."""
        counter = _NoOpCounter()
        counter.add(1)
        counter.add(100)

    def test_add_with_float(self) -> None:
        """Test add with float value."""
        counter = _NoOpCounter()
        counter.add(1.5)
        counter.add(99.99)

    def test_add_with_attributes(self) -> None:
        """Test add with attributes."""
        counter = _NoOpCounter()
        counter.add(1, attributes={"method": "GET"})
        counter.add(1, attributes={"method": "POST", "status": 200})


class TestNoOpHistogram:
    """Tests for _NoOpHistogram."""

    def test_record_with_int(self) -> None:
        """Test record with integer value."""
        histogram = _NoOpHistogram()
        histogram.record(100)
        histogram.record(500)

    def test_record_with_float(self) -> None:
        """Test record with float value."""
        histogram = _NoOpHistogram()
        histogram.record(0.5)
        histogram.record(123.456)

    def test_record_with_attributes(self) -> None:
        """Test record with attributes."""
        histogram = _NoOpHistogram()
        histogram.record(100, attributes={"endpoint": "/api/users"})
        histogram.record(50, attributes={"endpoint": "/api/items", "method": "GET"})
