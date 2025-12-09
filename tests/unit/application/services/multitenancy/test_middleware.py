"""Unit tests for TenantMiddleware.

**Task: Phase 3 - Application Layer Tests**
**Requirements: 1.4**
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.services.multitenancy.middleware.middleware import (
    TENANT_ID_MAX_LENGTH,
    TenantMiddleware,
    require_tenant,
)


class TestTenantMiddleware:
    """Tests for TenantMiddleware."""

    @pytest.fixture
    def mock_app(self) -> AsyncMock:
        """Create mock ASGI app."""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app: AsyncMock) -> TenantMiddleware:
        """Create middleware instance."""
        return TenantMiddleware(mock_app)

    @pytest.mark.asyncio
    async def test_extracts_tenant_from_header(
        self, middleware: TenantMiddleware, mock_app: AsyncMock
    ) -> None:
        """Should extract tenant ID from header."""
        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"tenant-123")],
        }

        with patch(
            "application.services.multitenancy.middleware.middleware.TenantContext"
        ) as mock_context:
            mock_context.return_value.__aenter__ = AsyncMock()
            mock_context.return_value.__aexit__ = AsyncMock()

            await middleware(scope, AsyncMock(), AsyncMock())

            mock_context.assert_called_once_with("tenant-123")

    @pytest.mark.asyncio
    async def test_passes_through_non_http(
        self, middleware: TenantMiddleware, mock_app: AsyncMock
    ) -> None:
        """Should pass through non-HTTP requests."""
        scope = {"type": "websocket"}

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_through_without_tenant(
        self, middleware: TenantMiddleware, mock_app: AsyncMock
    ) -> None:
        """Should pass through when no tenant ID found."""
        scope = {
            "type": "http",
            "headers": [],
        }

        await middleware(scope, AsyncMock(), AsyncMock())

        mock_app.assert_called_once()

    def test_sanitize_valid_tenant_id(self, middleware: TenantMiddleware) -> None:
        """Should accept valid tenant ID."""
        result = middleware._sanitize_tenant_id("valid-tenant_123")

        assert result == "valid-tenant_123"

    def test_sanitize_strips_whitespace(self, middleware: TenantMiddleware) -> None:
        """Should strip whitespace from tenant ID."""
        result = middleware._sanitize_tenant_id("  tenant-123  ")

        assert result == "tenant-123"

    def test_sanitize_rejects_empty(self, middleware: TenantMiddleware) -> None:
        """Should reject empty tenant ID."""
        result = middleware._sanitize_tenant_id("")

        assert result is None

    def test_sanitize_rejects_whitespace_only(self, middleware: TenantMiddleware) -> None:
        """Should reject whitespace-only tenant ID."""
        result = middleware._sanitize_tenant_id("   ")

        assert result is None

    def test_sanitize_rejects_too_long(self, middleware: TenantMiddleware) -> None:
        """Should reject tenant ID exceeding max length."""
        long_id = "a" * (TENANT_ID_MAX_LENGTH + 1)

        result = middleware._sanitize_tenant_id(long_id)

        assert result is None

    def test_sanitize_rejects_invalid_chars(self, middleware: TenantMiddleware) -> None:
        """Should reject tenant ID with invalid characters."""
        result = middleware._sanitize_tenant_id("tenant/../../../etc/passwd")

        assert result is None

    def test_sanitize_rejects_sql_injection(self, middleware: TenantMiddleware) -> None:
        """Should reject SQL injection attempts."""
        result = middleware._sanitize_tenant_id("tenant'; DROP TABLE users;--")

        assert result is None

    def test_extract_from_path_param(self, mock_app: AsyncMock) -> None:
        """Should extract tenant ID from path parameter."""
        middleware = TenantMiddleware(mock_app, path_param="tenant_id")
        scope = {
            "type": "http",
            "headers": [],
            "path_params": {"tenant_id": "path-tenant"},
        }

        tenant_id = middleware._extract_tenant_id(scope)

        assert tenant_id == "path-tenant"

    def test_header_takes_precedence_over_path(self, mock_app: AsyncMock) -> None:
        """Header should take precedence over path parameter."""
        middleware = TenantMiddleware(mock_app, path_param="tenant_id")
        scope = {
            "type": "http",
            "headers": [(b"x-tenant-id", b"header-tenant")],
            "path_params": {"tenant_id": "path-tenant"},
        }

        tenant_id = middleware._extract_tenant_id(scope)

        assert tenant_id == "header-tenant"


class TestRequireTenant:
    """Tests for require_tenant decorator."""

    @pytest.mark.asyncio
    async def test_raises_when_no_tenant(self) -> None:
        """Should raise ValueError when no tenant set."""

        @require_tenant
        async def protected_func() -> str:
            return "result"

        with patch(
            "application.services.multitenancy.middleware.middleware.get_current_tenant",
            return_value=None,
        ):
            with pytest.raises(ValueError, match="Tenant context required but not set"):
                await protected_func()

    @pytest.mark.asyncio
    async def test_allows_when_tenant_set(self) -> None:
        """Should allow execution when tenant is set."""

        @require_tenant
        async def protected_func() -> str:
            return "result"

        with patch(
            "application.services.multitenancy.middleware.middleware.get_current_tenant",
            return_value="tenant-123",
        ):
            result = await protected_func()

            assert result == "result"
