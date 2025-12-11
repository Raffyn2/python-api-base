"""Tests for idempotency middleware module.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 23.1, 23.5, 23.6**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.responses import JSONResponse

from infrastructure.idempotency.handler import IdempotencyConfig
from infrastructure.idempotency.middleware import IdempotencyMiddleware


class TestIdempotencyMiddlewareInit:
    """Tests for IdempotencyMiddleware initialization."""

    def test_default_methods(self) -> None:
        """Test default HTTP methods."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        assert middleware._methods == {"POST", "PATCH", "PUT"}

    def test_custom_methods(self) -> None:
        """Test custom HTTP methods."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app, methods={"POST"})
        assert middleware._methods == {"POST"}

    def test_default_exclude_paths(self) -> None:
        """Test default excluded paths."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        assert "/health" in middleware._exclude_paths
        assert "/metrics" in middleware._exclude_paths
        assert "/docs" in middleware._exclude_paths
        assert "/redoc" in middleware._exclude_paths

    def test_custom_exclude_paths(self) -> None:
        """Test custom excluded paths."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app, exclude_paths={"/custom"})
        assert middleware._exclude_paths == {"/custom"}

    def test_required_endpoints(self) -> None:
        """Test required endpoints configuration."""
        app = MagicMock()
        endpoints = {"/api/payments", "/api/orders"}
        middleware = IdempotencyMiddleware(app, required_endpoints=endpoints)
        assert middleware._required_endpoints == endpoints

    def test_with_handler(self) -> None:
        """Test initialization with handler."""
        app = MagicMock()
        handler = MagicMock()
        handler._config = IdempotencyConfig()
        middleware = IdempotencyMiddleware(app, handler=handler)
        assert middleware._handler is handler


class TestIdempotencyMiddlewareHelpers:
    """Tests for IdempotencyMiddleware helper methods."""

    def test_create_error_response(self) -> None:
        """Test error response creation."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        response = middleware._create_error_response(
            error_type="test-error",
            title="Test Error",
            detail="Test detail",
            status=400,
        )
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    def test_create_conflict_response(self) -> None:
        """Test conflict response creation."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        response = middleware._create_conflict_response()
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422

    def test_create_key_missing_response(self) -> None:
        """Test key missing response creation."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        response = middleware._create_key_missing_response()
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    def test_should_handle_post(self) -> None:
        """Test should_handle for POST request."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/users"
        assert middleware._should_handle(request) is True

    def test_should_handle_get(self) -> None:
        """Test should_handle for GET request."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/users"
        assert middleware._should_handle(request) is False

    def test_should_handle_excluded_path(self) -> None:
        """Test should_handle for excluded path."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/health"
        assert middleware._should_handle(request) is False

    def test_is_required_true(self) -> None:
        """Test is_required for required endpoint."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app, required_endpoints={"/api/payments"})
        assert middleware._is_required("/api/payments/123") is True

    def test_is_required_false(self) -> None:
        """Test is_required for non-required endpoint."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app, required_endpoints={"/api/payments"})
        assert middleware._is_required("/api/users") is False

    def test_get_handler_from_init(self) -> None:
        """Test _get_handler returns handler from init."""
        app = MagicMock()
        handler = MagicMock()
        handler._config = IdempotencyConfig()
        middleware = IdempotencyMiddleware(app, handler=handler)
        request = MagicMock()
        assert middleware._get_handler(request) is handler

    def test_get_handler_from_app_state(self) -> None:
        """Test _get_handler returns handler from app.state."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        state_handler = MagicMock()
        request.app.state.idempotency_handler = state_handler
        assert middleware._get_handler(request) is state_handler

    def test_get_handler_none(self) -> None:
        """Test _get_handler returns None when no handler."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        del request.app.state.idempotency_handler
        assert middleware._get_handler(request) is None


class TestIdempotencyMiddlewareDispatch:
    """Tests for IdempotencyMiddleware dispatch method."""

    @pytest.mark.asyncio
    async def test_dispatch_skip_get_request(self) -> None:
        """Test dispatch skips GET requests."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/users"

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_skip_excluded_path(self) -> None:
        """Test dispatch skips excluded paths."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/health"

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_no_handler(self) -> None:
        """Test dispatch when no handler available."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/users"
        del request.app.state.idempotency_handler

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_no_key_not_required(self) -> None:
        """Test dispatch without key on non-required endpoint."""
        app = MagicMock()
        handler = MagicMock()
        handler._config = IdempotencyConfig()
        middleware = IdempotencyMiddleware(app, handler=handler)
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/users"
        request.headers.get.return_value = None

        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_no_key_required(self) -> None:
        """Test dispatch without key on required endpoint."""
        app = MagicMock()
        handler = MagicMock()
        handler._config = IdempotencyConfig()
        middleware = IdempotencyMiddleware(app, handler=handler, required_endpoints={"/api/payments"})
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/payments"
        request.headers.get.return_value = None

        call_next = AsyncMock(return_value=MagicMock())
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 400
        call_next.assert_not_called()


class TestIdempotencyMiddlewareCachedRecord:
    """Tests for _handle_cached_record method."""

    @pytest.mark.asyncio
    async def test_handle_cached_record_conflict(self) -> None:
        """Test handling cached record with hash conflict."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        record = MagicMock()
        record.request_hash = "hash1"

        response = await middleware._handle_cached_record(
            record=record,
            request_hash="hash2",
            idempotency_key="key-123",
            path="/api/users",
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_handle_cached_record_replay(self) -> None:
        """Test handling cached record with matching hash."""
        app = MagicMock()
        middleware = IdempotencyMiddleware(app)
        record = MagicMock()
        record.request_hash = "hash1"
        record.response_body = '{"id": 1}'
        record.status_code = 201

        response = await middleware._handle_cached_record(
            record=record,
            request_hash="hash1",
            idempotency_key="key-123",
            path="/api/users",
        )
        assert response.status_code == 201
        assert "X-Idempotent-Replayed" in response.headers
