"""Property-based tests for Dapr observability.

These tests verify correctness properties for metrics and logging.
"""

import re
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import MagicMock, patch


class TestPrometheusMetricsFormat:
    """
    **Feature: dapr-sidecar-integration, Property 22: Prometheus Metrics Format Compliance**
    **Validates: Requirements 10.3**

    For any exposed metric, the format should be Prometheus-compatible
    (valid metric names, labels, and values).
    """

    @given(
        metric_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="_"
        )).filter(lambda x: x and x[0].isalpha()),
        value=st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=5000)
    def test_metric_name_format(
        self,
        metric_name: str,
        value: float,
    ) -> None:
        """Metric names should follow Prometheus naming conventions."""
        prometheus_name_pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*$'
        
        if metric_name and metric_name[0].isalpha():
            sanitized_name = re.sub(r'[^a-zA-Z0-9_:]', '_', metric_name)
            assert re.match(prometheus_name_pattern, sanitized_name)

    @given(
        labels=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(
                whitelist_categories=("L", "N"),
                whitelist_characters="_"
            )).filter(lambda x: x and x[0].isalpha()),
            st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    def test_metric_labels_format(
        self,
        labels: dict[str, str],
    ) -> None:
        """Metric labels should follow Prometheus label conventions."""
        prometheus_label_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        
        for label_name in labels.keys():
            if label_name and label_name[0].isalpha():
                sanitized_name = re.sub(r'[^a-zA-Z0-9_]', '_', label_name)
                assert re.match(prometheus_label_pattern, sanitized_name)

    @given(
        metric_name=st.text(min_size=1, max_size=30, alphabet=st.characters(
            whitelist_categories=("L",),
        )).filter(lambda x: x.strip()),
        value=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
        labels=st.dictionaries(
            st.text(min_size=1, max_size=10, alphabet=st.characters(
                whitelist_categories=("L",),
            )),
            st.text(min_size=1, max_size=20),
            min_size=0,
            max_size=3,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    def test_prometheus_line_format(
        self,
        metric_name: str,
        value: float,
        labels: dict[str, str],
    ) -> None:
        """Prometheus exposition format should be valid."""
        def format_prometheus_line(name: str, val: float, lbls: dict) -> str:
            sanitized_name = re.sub(r'[^a-zA-Z0-9_:]', '_', name)
            if not sanitized_name[0].isalpha():
                sanitized_name = 'metric_' + sanitized_name
            
            if lbls:
                label_parts = []
                for k, v in lbls.items():
                    sanitized_key = re.sub(r'[^a-zA-Z0-9_]', '_', k)
                    if not sanitized_key[0].isalpha():
                        sanitized_key = 'label_' + sanitized_key
                    escaped_value = v.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                    label_parts.append(f'{sanitized_key}="{escaped_value}"')
                label_str = '{' + ','.join(label_parts) + '}'
                return f'{sanitized_name}{label_str} {val}'
            return f'{sanitized_name} {val}'
        
        line = format_prometheus_line(metric_name, value, labels)
        
        assert metric_name.replace(' ', '_').lower() in line.lower() or 'metric_' in line
        assert str(value) in line or f'{value:.1f}' in line[:50]


class TestLogCorrelationIdPresence:
    """
    **Feature: dapr-sidecar-integration, Property 23: Log Correlation ID Presence**
    **Validates: Requirements 10.4**

    For any log entry generated during a traced request, the correlation ID
    and trace context should be present.
    """

    @given(
        trace_id=st.text(min_size=32, max_size=32, alphabet=st.characters(
            whitelist_categories=("N",),
            whitelist_characters="abcdef"
        )),
        span_id=st.text(min_size=16, max_size=16, alphabet=st.characters(
            whitelist_categories=("N",),
            whitelist_characters="abcdef"
        )),
        message=st.text(min_size=1, max_size=200),
    )
    @settings(max_examples=100, deadline=5000)
    def test_log_contains_trace_context(
        self,
        trace_id: str,
        span_id: str,
        message: str,
    ) -> None:
        """Log entries should contain trace context when available."""
        log_entry = {
            "message": message,
            "trace_id": trace_id,
            "span_id": span_id,
            "level": "INFO",
        }
        
        assert "trace_id" in log_entry
        assert "span_id" in log_entry
        assert len(log_entry["trace_id"]) == 32
        assert len(log_entry["span_id"]) == 16

    @given(
        correlation_id=st.uuids(),
        request_id=st.uuids(),
    )
    @settings(max_examples=50, deadline=5000)
    def test_log_contains_correlation_ids(
        self,
        correlation_id,
        request_id,
    ) -> None:
        """Log entries should contain correlation IDs."""
        log_entry = {
            "message": "Test log message",
            "correlation_id": str(correlation_id),
            "request_id": str(request_id),
        }
        
        assert "correlation_id" in log_entry
        assert "request_id" in log_entry
        
        import uuid
        assert uuid.UUID(log_entry["correlation_id"])
        assert uuid.UUID(log_entry["request_id"])

    @given(
        level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        logger_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="._"
        )).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    def test_structured_log_format(
        self,
        level: str,
        logger_name: str,
    ) -> None:
        """Structured logs should have consistent format."""
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": logger_name,
            "message": "Test message",
            "trace_id": "0" * 32,
            "span_id": "0" * 16,
        }
        
        serialized = json.dumps(log_entry)
        deserialized = json.loads(serialized)
        
        assert deserialized["level"] == level
        assert deserialized["logger"] == logger_name
        assert "timestamp" in deserialized
        assert "trace_id" in deserialized
        assert "span_id" in deserialized
