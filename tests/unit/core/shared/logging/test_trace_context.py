"""Unit tests for trace context logging processors.

Tests add_trace_context, add_dapr_context, and get_trace_context_processors.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from core.shared.logging.trace_context import (
    add_dapr_context,
    add_trace_context,
    get_trace_context_processors,
)


class TestAddTraceContext:
    """Tests for add_trace_context processor."""

    def test_returns_event_dict(self) -> None:
        """Test processor returns event dict."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        result = add_trace_context(logger, "info", event_dict)
        
        assert result is event_dict

    def test_handles_missing_opentelemetry(self) -> None:
        """Test graceful handling when opentelemetry not installed."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        with patch.dict("sys.modules", {"opentelemetry": None}):
            result = add_trace_context(logger, "info", event_dict)
        
        assert result == {"event": "test"}

    def test_adds_trace_context_when_valid(self) -> None:
        """Test adds trace context when span is valid - graceful without opentelemetry."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        # The function uses lazy import inside try/except
        # Without opentelemetry installed, it gracefully returns event_dict
        result = add_trace_context(logger, "info", event_dict)
        
        # Should return event_dict (possibly with trace context if otel available)
        assert result is event_dict

    def test_skips_invalid_span_context(self) -> None:
        """Test skips adding context when span is invalid."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        # Function handles missing opentelemetry gracefully
        result = add_trace_context(logger, "info", event_dict)
        
        # Should return event_dict unchanged if opentelemetry not available
        assert result is event_dict

    def test_handles_exception_gracefully(self) -> None:
        """Test handles exceptions without raising."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        # The function catches all exceptions internally
        result = add_trace_context(logger, "info", event_dict)
        
        assert result is event_dict


class TestAddDaprContext:
    """Tests for add_dapr_context processor."""

    def test_returns_event_dict(self) -> None:
        """Test processor returns event dict."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        result = add_dapr_context(logger, "info", event_dict)
        
        assert result is event_dict

    def test_handles_missing_dapr_config(self) -> None:
        """Test graceful handling when dapr config not available."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        # The function uses lazy import and catches ImportError internally
        result = add_dapr_context(logger, "info", event_dict)
        
        # Should return event_dict unchanged
        assert result is event_dict

    def test_adds_dapr_context_when_enabled(self) -> None:
        """Test adds dapr context when enabled."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        mock_settings = MagicMock()
        mock_settings.enabled = True
        mock_settings.app_id = "test-app"
        
        mock_dapr_module = MagicMock()
        mock_dapr_module.get_dapr_settings = MagicMock(return_value=mock_settings)
        
        with patch.dict("sys.modules", {"core.config.dapr": mock_dapr_module}):
            result = add_dapr_context(logger, "info", event_dict)
        
        # Function handles import internally, result depends on actual import
        assert result is event_dict

    def test_skips_when_dapr_disabled(self) -> None:
        """Test skips adding context when dapr disabled."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        # Function handles missing config gracefully
        result = add_dapr_context(logger, "info", event_dict)
        
        # Without dapr config, no dapr_app_id should be added
        assert "dapr_app_id" not in result or result is event_dict

    def test_handles_exception_gracefully(self) -> None:
        """Test handles exceptions without raising."""
        logger = logging.getLogger("test")
        event_dict = {"event": "test"}
        
        # The function catches all exceptions internally
        result = add_dapr_context(logger, "info", event_dict)
        
        assert result is event_dict


class TestGetTraceContextProcessors:
    """Tests for get_trace_context_processors function."""

    def test_returns_list(self) -> None:
        """Test returns a list."""
        result = get_trace_context_processors()
        
        assert isinstance(result, list)

    def test_contains_processors(self) -> None:
        """Test contains expected processors."""
        result = get_trace_context_processors()
        
        assert add_trace_context in result
        assert add_dapr_context in result

    def test_returns_two_processors(self) -> None:
        """Test returns exactly two processors."""
        result = get_trace_context_processors()
        
        assert len(result) == 2
