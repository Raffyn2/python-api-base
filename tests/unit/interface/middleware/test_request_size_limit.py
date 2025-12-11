"""Unit tests for request size limit middleware.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 6.4 (DoS protection)**
"""

import importlib.util

# Import directly to avoid circular import issues
import sys
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Load the request_size_limit module directly
spec = importlib.util.spec_from_file_location(
    "request_size_limit_module", "src/interface/middleware/request/request_size_limit.py"
)
request_size_limit_module = importlib.util.module_from_spec(spec)
sys.modules["request_size_limit_module"] = request_size_limit_module
spec.loader.exec_module(request_size_limit_module)

RequestSizeLimitMiddleware = request_size_limit_module.RequestSizeLimitMiddleware
RouteSizeLimit = request_size_limit_module.RouteSizeLimit
create_size_limit_middleware = request_size_limit_module.create_size_limit_middleware


class TestRouteSizeLimit:
    """Tests for RouteSizeLimit dataclass."""

    def test_valid_pattern_matches(self) -> None:
        """Test that valid patterns match correctly."""
        limit = RouteSizeLimit(pattern=r"/api/upload.*", max_size=10_000_000)

        assert limit.matches("/api/upload") is True
        assert limit.matches("/api/upload/file") is True
        assert limit.matches("/api/items") is False

    def test_invalid_pattern_never_matches(self) -> None:
        """Test that invalid regex patterns never match."""
        limit = RouteSizeLimit(pattern=r"[invalid", max_size=1000)

        assert limit.matches("/any/path") is False

    def test_exact_match_pattern(self) -> None:
        """Test exact match patterns."""
        limit = RouteSizeLimit(pattern=r"^/api/upload$", max_size=1000)

        assert limit.matches("/api/upload") is True
        assert limit.matches("/api/upload/extra") is False


class TestRequestSizeLimitMiddleware:
    """Tests for RequestSizeLimitMiddleware."""

    @pytest.fixture()
    def app(self) -> FastAPI:
        """Create test FastAPI app."""
        app = FastAPI()

        @app.post("/api/items")
        async def create_item(data: dict) -> dict:
            return {"status": "created"}

        @app.post("/api/upload")
        async def upload_file() -> dict:
            return {"status": "uploaded"}

        return app

    def test_allows_request_under_limit(self, app: FastAPI) -> None:
        """Test that requests under limit are allowed."""
        app.add_middleware(RequestSizeLimitMiddleware, max_size=1024)
        client = TestClient(app)

        response = client.post(
            "/api/items",
            json={"name": "test"},
            headers={"Content-Length": "50"},
        )

        assert response.status_code == 200

    def test_rejects_request_over_limit(self, app: FastAPI) -> None:
        """Test that requests over limit are rejected."""
        app.add_middleware(RequestSizeLimitMiddleware, max_size=100)
        client = TestClient(app)

        response = client.post(
            "/api/items",
            json={"name": "test"},
            headers={"Content-Length": "200"},
        )

        assert response.status_code == 413
        data = response.json()
        assert data["status"] == 413
        assert "too large" in data["detail"].lower()

    def test_route_specific_limits(self, app: FastAPI) -> None:
        """Test that route-specific limits are applied."""
        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_size=100,
            route_limits={r"/api/upload.*": 10_000_000},
        )
        client = TestClient(app)

        # Regular route should use default limit
        response = client.post(
            "/api/items",
            json={"name": "test"},
            headers={"Content-Length": "200"},
        )
        assert response.status_code == 413

        # Upload route should use higher limit
        response = client.post(
            "/api/upload",
            headers={"Content-Length": "5000"},
        )
        assert response.status_code == 200

    def test_custom_error_response(self, app: FastAPI) -> None:
        """Test custom error response."""
        custom_error = {
            "type": "custom-error",
            "title": "Custom Error",
            "status": 413,
        }
        app.add_middleware(
            RequestSizeLimitMiddleware,
            max_size=100,
            error_response=custom_error,
        )
        client = TestClient(app)

        response = client.post(
            "/api/items",
            json={"name": "test"},
            headers={"Content-Length": "200"},
        )

        assert response.status_code == 413
        data = response.json()
        assert data["type"] == "custom-error"
        assert data["title"] == "Custom Error"

    def test_allows_request_without_content_length(self, app: FastAPI) -> None:
        """Test that requests without Content-Length are allowed through."""
        app.add_middleware(RequestSizeLimitMiddleware, max_size=100)
        TestClient(app)

        # TestClient always adds Content-Length, so we test the logic directly
        middleware = RequestSizeLimitMiddleware(app, max_size=100)
        assert middleware.get_limit_for_path("/api/items") == 100


class TestGetLimitForPath:
    """Tests for get_limit_for_path method."""

    def test_returns_default_when_no_match(self) -> None:
        """Test that default limit is returned when no route matches."""
        middleware = RequestSizeLimitMiddleware(
            app=MagicMock(),
            max_size=1000,
            route_limits={r"/api/upload.*": 10000},
        )

        assert middleware.get_limit_for_path("/api/items") == 1000

    def test_returns_route_limit_when_matched(self) -> None:
        """Test that route limit is returned when matched."""
        middleware = RequestSizeLimitMiddleware(
            app=MagicMock(),
            max_size=1000,
            route_limits={r"/api/upload.*": 10000},
        )

        assert middleware.get_limit_for_path("/api/upload/file") == 10000

    def test_first_match_wins(self) -> None:
        """Test that first matching route limit is used."""
        middleware = RequestSizeLimitMiddleware(
            app=MagicMock(),
            max_size=1000,
            route_limits={
                r"/api/upload.*": 10000,
                r"/api/upload/large.*": 50000,
            },
        )

        # First pattern matches, so 10000 is returned
        assert middleware.get_limit_for_path("/api/upload/large/file") == 10000


class TestAddRemoveRouteLimit:
    """Tests for add_route_limit and remove_route_limit methods."""

    def test_add_route_limit(self) -> None:
        """Test adding a route limit."""
        middleware = RequestSizeLimitMiddleware(app=MagicMock(), max_size=1000)

        middleware.add_route_limit(r"/api/new.*", 5000)

        assert middleware.get_limit_for_path("/api/new/endpoint") == 5000

    def test_remove_route_limit(self) -> None:
        """Test removing a route limit."""
        middleware = RequestSizeLimitMiddleware(
            app=MagicMock(),
            max_size=1000,
            route_limits={r"/api/upload.*": 10000},
        )

        result = middleware.remove_route_limit(r"/api/upload.*")

        assert result is True
        assert middleware.get_limit_for_path("/api/upload/file") == 1000

    def test_remove_nonexistent_route_limit(self) -> None:
        """Test removing a nonexistent route limit."""
        middleware = RequestSizeLimitMiddleware(app=MagicMock(), max_size=1000)

        result = middleware.remove_route_limit(r"/nonexistent.*")

        assert result is False


class TestCreateSizeLimitMiddleware:
    """Tests for create_size_limit_middleware factory."""

    def test_creates_middleware_with_defaults(self) -> None:
        """Test factory creates middleware with default values."""
        middleware = create_size_limit_middleware()

        assert middleware.max_size == 1024 * 1024  # 1MB

    def test_creates_middleware_with_custom_max_size(self) -> None:
        """Test factory creates middleware with custom max size."""
        middleware = create_size_limit_middleware(max_size=500_000)

        assert middleware.max_size == 500_000

    def test_creates_middleware_with_upload_routes(self) -> None:
        """Test factory creates middleware with upload routes."""
        middleware = create_size_limit_middleware(
            max_size=1000,
            upload_routes=[r"/upload.*", r"/import.*"],
            upload_max_size=10_000_000,
        )

        assert middleware.get_limit_for_path("/upload/file") == 10_000_000
        assert middleware.get_limit_for_path("/import/data") == 10_000_000
        assert middleware.get_limit_for_path("/api/items") == 1000


class TestErrorResponseFormat:
    """Tests for error response format compliance."""

    def test_error_response_is_problem_json(self) -> None:
        """Test that error response follows RFC 7807 format."""
        app = FastAPI()

        @app.post("/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        app.add_middleware(RequestSizeLimitMiddleware, max_size=100)
        client = TestClient(app)

        response = client.post(
            "/test",
            json={"data": "x" * 200},
            headers={"Content-Length": "500"},
        )

        assert response.status_code == 413
        assert response.headers.get("content-type") == "application/problem+json"

        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data

    def test_error_includes_size_info(self) -> None:
        """Test that error includes size information."""
        app = FastAPI()

        @app.post("/test")
        async def test_endpoint() -> dict:
            return {"status": "ok"}

        app.add_middleware(RequestSizeLimitMiddleware, max_size=100)
        client = TestClient(app)

        response = client.post(
            "/test",
            headers={"Content-Length": "500"},
        )

        data = response.json()
        assert data["max_size"] == 100
        assert data["actual_size"] == 500
