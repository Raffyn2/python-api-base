"""Unit tests for multitenancy tenant context.

Tests TenantContext, get_current_tenant, set_current_tenant.
"""

import pytest

from application.services.multitenancy.models.models import (
    TenantContext,
    get_current_tenant,
    set_current_tenant,
)


class TestTenantContextFunctions:
    """Tests for tenant context functions."""

    def test_get_current_tenant_default(self) -> None:
        """Test default tenant is None."""
        # Reset context first
        set_current_tenant(None)
        
        result = get_current_tenant()
        
        assert result is None

    def test_set_and_get_tenant(self) -> None:
        """Test setting and getting tenant."""
        set_current_tenant("tenant-123")
        
        result = get_current_tenant()
        
        assert result == "tenant-123"
        
        # Cleanup
        set_current_tenant(None)

    def test_set_tenant_to_none(self) -> None:
        """Test clearing tenant."""
        set_current_tenant("tenant-123")
        set_current_tenant(None)
        
        result = get_current_tenant()
        
        assert result is None


class TestTenantContext:
    """Tests for TenantContext context manager."""

    def test_sync_context_manager(self) -> None:
        """Test synchronous context manager."""
        set_current_tenant(None)
        
        with TenantContext("tenant-456"):
            assert get_current_tenant() == "tenant-456"
        
        assert get_current_tenant() is None

    def test_sync_context_restores_previous(self) -> None:
        """Test context restores previous tenant."""
        set_current_tenant("tenant-original")
        
        with TenantContext("tenant-new"):
            assert get_current_tenant() == "tenant-new"
        
        assert get_current_tenant() == "tenant-original"
        
        # Cleanup
        set_current_tenant(None)

    def test_nested_contexts(self) -> None:
        """Test nested tenant contexts."""
        set_current_tenant(None)
        
        with TenantContext("tenant-1"):
            assert get_current_tenant() == "tenant-1"
            
            with TenantContext("tenant-2"):
                assert get_current_tenant() == "tenant-2"
            
            assert get_current_tenant() == "tenant-1"
        
        assert get_current_tenant() is None

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        """Test asynchronous context manager."""
        set_current_tenant(None)
        
        async with TenantContext("tenant-async"):
            assert get_current_tenant() == "tenant-async"
        
        assert get_current_tenant() is None

    @pytest.mark.asyncio
    async def test_async_context_restores_previous(self) -> None:
        """Test async context restores previous tenant."""
        set_current_tenant("tenant-original")
        
        async with TenantContext("tenant-async"):
            assert get_current_tenant() == "tenant-async"
        
        assert get_current_tenant() == "tenant-original"
        
        # Cleanup
        set_current_tenant(None)

    def test_context_returns_self(self) -> None:
        """Test context manager returns self."""
        ctx = TenantContext("tenant-123")
        
        with ctx as entered:
            assert entered is ctx
            assert entered.tenant_id == "tenant-123"
        
        # Cleanup
        set_current_tenant(None)

    @pytest.mark.asyncio
    async def test_async_context_returns_self(self) -> None:
        """Test async context manager returns self."""
        ctx = TenantContext("tenant-123")
        
        async with ctx as entered:
            assert entered is ctx
            assert entered.tenant_id == "tenant-123"
        
        # Cleanup
        set_current_tenant(None)

    def test_context_on_exception(self) -> None:
        """Test context restores tenant on exception."""
        set_current_tenant("tenant-original")
        
        with pytest.raises(ValueError):
            with TenantContext("tenant-error"):
                assert get_current_tenant() == "tenant-error"
                raise ValueError("Test error")
        
        assert get_current_tenant() == "tenant-original"
        
        # Cleanup
        set_current_tenant(None)
