"""Unit tests for feature flags middleware.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 19.2 (Feature Flags)**
"""

import importlib.util

# Import directly to avoid circular import issues
import sys
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest

# Load the feature_flags module directly
spec = importlib.util.spec_from_file_location(
    "feature_flags_module", "src/interface/middleware/production/feature_flags.py"
)
feature_flags_module = importlib.util.module_from_spec(spec)
sys.modules["feature_flags_module"] = feature_flags_module
spec.loader.exec_module(feature_flags_module)

FeatureFlagMiddleware = feature_flags_module.FeatureFlagMiddleware
is_feature_enabled = feature_flags_module.is_feature_enabled


class TestFeatureFlagMiddleware:
    """Tests for FeatureFlagMiddleware."""

    @pytest.fixture()
    def mock_evaluator(self) -> MagicMock:
        """Create mock feature flag evaluator."""
        evaluator = MagicMock()
        evaluator.is_enabled = MagicMock(return_value=True)
        return evaluator

    @pytest.fixture()
    def app(self, mock_evaluator: MagicMock) -> FastAPI:
        """Create test FastAPI app with feature flag middleware."""
        app = FastAPI()
        app.add_middleware(FeatureFlagMiddleware, evaluator=mock_evaluator)

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        return app

    def test_middleware_stores_evaluator_in_state(self, mock_evaluator: MagicMock) -> None:
        """Test that evaluator is stored in request state."""
        app = FastAPI()
        stored_evaluator = None

        @app.get("/check")
        async def check_endpoint(request: StarletteRequest) -> dict:
            nonlocal stored_evaluator
            stored_evaluator = getattr(request.state, "feature_flags", None)
            return {"status": "ok"}

        app.add_middleware(FeatureFlagMiddleware, evaluator=mock_evaluator)
        client = TestClient(app)

        response = client.get("/check")

        assert response.status_code == 200
        assert stored_evaluator == mock_evaluator

    def test_middleware_stores_context_in_state(self, mock_evaluator: MagicMock) -> None:
        """Test that evaluation context is stored in request state."""
        app = FastAPI()
        stored_context = None

        @app.get("/check")
        async def check_endpoint(request: StarletteRequest) -> dict:
            nonlocal stored_context
            stored_context = getattr(request.state, "feature_context", None)
            return {"status": "ok"}

        app.add_middleware(FeatureFlagMiddleware, evaluator=mock_evaluator)
        client = TestClient(app)

        response = client.get("/check")

        assert response.status_code == 200
        assert stored_context is not None
        assert stored_context.attributes["path"] == "/check"
        assert stored_context.attributes["method"] == "GET"

    def test_middleware_extracts_user_id_from_header(self, mock_evaluator: MagicMock) -> None:
        """Test that user ID is extracted from X-User-ID header."""
        app = FastAPI()
        stored_context = None

        @app.get("/check")
        async def check_endpoint(request: StarletteRequest) -> dict:
            nonlocal stored_context
            stored_context = getattr(request.state, "feature_context", None)
            return {"status": "ok"}

        app.add_middleware(FeatureFlagMiddleware, evaluator=mock_evaluator)
        client = TestClient(app)

        response = client.get("/check", headers={"X-User-ID": "user-123"})

        assert response.status_code == 200
        assert stored_context.user_id == "user-123"

    def test_middleware_handles_missing_user_id(self, mock_evaluator: MagicMock) -> None:
        """Test that missing user ID is handled gracefully."""
        app = FastAPI()
        stored_context = None

        @app.get("/check")
        async def check_endpoint(request: StarletteRequest) -> dict:
            nonlocal stored_context
            stored_context = getattr(request.state, "feature_context", None)
            return {"status": "ok"}

        app.add_middleware(FeatureFlagMiddleware, evaluator=mock_evaluator)
        client = TestClient(app)

        response = client.get("/check")

        assert response.status_code == 200
        assert stored_context.user_id is None


class TestIsFeatureEnabled:
    """Tests for is_feature_enabled helper function."""

    def test_returns_true_when_enabled(self) -> None:
        """Test that True is returned when feature is enabled."""
        request = MagicMock()
        evaluator = MagicMock()
        evaluator.is_enabled = MagicMock(return_value=True)
        context = MagicMock()

        request.state.feature_flags = evaluator
        request.state.feature_context = context

        result = is_feature_enabled(request, "test_feature")

        assert result is True
        evaluator.is_enabled.assert_called_once_with("test_feature", context)

    def test_returns_false_when_disabled(self) -> None:
        """Test that False is returned when feature is disabled."""
        request = MagicMock()
        evaluator = MagicMock()
        evaluator.is_enabled = MagicMock(return_value=False)
        context = MagicMock()

        request.state.feature_flags = evaluator
        request.state.feature_context = context

        result = is_feature_enabled(request, "test_feature")

        assert result is False

    def test_returns_false_when_no_evaluator(self) -> None:
        """Test that False is returned when evaluator is not set."""
        request = MagicMock()
        request.state = MagicMock(spec=[])  # No feature_flags attribute

        result = is_feature_enabled(request, "test_feature")

        assert result is False

    def test_returns_false_when_no_context(self) -> None:
        """Test that False is returned when context is not set."""
        request = MagicMock()
        request.state.feature_flags = MagicMock()
        del request.state.feature_context

        result = is_feature_enabled(request, "test_feature")

        assert result is False


class TestFeatureFlagIntegration:
    """Integration tests for feature flag middleware."""

    def test_feature_flag_in_route_handler(self) -> None:
        """Test using feature flag in route handler."""
        evaluator = MagicMock()
        evaluator.is_enabled = MagicMock(side_effect=lambda key, ctx: key == "new_feature")

        app = FastAPI()
        app.add_middleware(FeatureFlagMiddleware, evaluator=evaluator)

        @app.get("/items")
        async def list_items(request: StarletteRequest) -> dict:
            if is_feature_enabled(request, "new_feature"):
                return {"version": "v2", "items": []}
            return {"version": "v1", "items": []}

        client = TestClient(app)

        response = client.get("/items")

        assert response.status_code == 200
        assert response.json()["version"] == "v2"

    def test_feature_flag_disabled_in_route_handler(self) -> None:
        """Test disabled feature flag in route handler."""
        evaluator = MagicMock()
        evaluator.is_enabled = MagicMock(return_value=False)

        app = FastAPI()
        app.add_middleware(FeatureFlagMiddleware, evaluator=evaluator)

        @app.get("/items")
        async def list_items(request: StarletteRequest) -> dict:
            if is_feature_enabled(request, "new_feature"):
                return {"version": "v2", "items": []}
            return {"version": "v1", "items": []}

        client = TestClient(app)

        response = client.get("/items")

        assert response.status_code == 200
        assert response.json()["version"] == "v1"
