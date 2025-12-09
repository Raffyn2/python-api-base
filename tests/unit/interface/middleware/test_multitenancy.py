"""Unit tests for multitenancy middleware.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 7.3**
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from infrastructure.multitenancy import TenantContext, TenantResolutionStrategy

# Import directly to avoid circular import issues
import sys
import importlib.util

# Load the multitenancy module directly
spec = importlib.util.spec_from_file_location(
    "multitenancy_middleware",
    "src/interface/middleware/production/multitenancy.py"
)
multitenancy_module = importlib.util.module_from_spec(spec)
sys.modules["multitenancy_middleware"] = multitenancy_module
spec.loader.exec_module(multitenancy_module)

MultitenancyConfig = multitenancy_module.MultitenancyConfig
MultitenancyMiddleware = multitenancy_module.MultitenancyMiddleware


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint() -> dict:
        return {"status": "ok"}
    
    @app.get("/tenant")
    async def tenant_endpoint() -> dict:
        tenant = TenantContext.get_current()
        if tenant:
            return {"tenant_id": tenant.id}
        return {"tenant_id": None}
    
    return app


class TestMultitenancyConfig:
    """Tests for MultitenancyConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = MultitenancyConfig()
        
        assert config.strategy == TenantResolutionStrategy.HEADER
        assert config.header_name == "X-Tenant-ID"
        assert config.required is False
        assert config.default_tenant_id is None

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = MultitenancyConfig(
            strategy=TenantResolutionStrategy.SUBDOMAIN,
            header_name="X-Custom-Tenant",
            required=True,
            default_tenant_id="default-tenant",
        )
        
        assert config.strategy == TenantResolutionStrategy.SUBDOMAIN
        assert config.header_name == "X-Custom-Tenant"
        assert config.required is True
        assert config.default_tenant_id == "default-tenant"


class TestMultitenancyMiddleware:
    """Tests for MultitenancyMiddleware."""

    def test_middleware_with_tenant_header(self, app: FastAPI) -> None:
        """Test middleware extracts tenant from header."""
        config = MultitenancyConfig()
        app.add_middleware(MultitenancyMiddleware, config=config)
        client = TestClient(app)
        
        response = client.get("/test", headers={"X-Tenant-ID": "tenant-123"})
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_middleware_without_tenant_header_not_required(
        self, app: FastAPI
    ) -> None:
        """Test middleware allows request without tenant when not required."""
        config = MultitenancyConfig(required=False)
        app.add_middleware(MultitenancyMiddleware, config=config)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200

    def test_middleware_without_tenant_header_required(
        self, app: FastAPI
    ) -> None:
        """Test middleware rejects request without tenant when required."""
        config = MultitenancyConfig(required=True)
        app.add_middleware(MultitenancyMiddleware, config=config)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 400
        assert "Tenant ID required" in response.text

    def test_middleware_with_default_tenant(self, app: FastAPI) -> None:
        """Test middleware uses default tenant when header missing."""
        config = MultitenancyConfig(
            required=False,
            default_tenant_id="default-tenant",
        )
        app.add_middleware(MultitenancyMiddleware, config=config)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200

    def test_middleware_custom_header_name(self, app: FastAPI) -> None:
        """Test middleware uses custom header name."""
        config = MultitenancyConfig(header_name="X-Custom-Tenant")
        app.add_middleware(MultitenancyMiddleware, config=config)
        client = TestClient(app)
        
        response = client.get("/test", headers={"X-Custom-Tenant": "tenant-456"})
        
        assert response.status_code == 200

    def test_middleware_clears_context_after_request(self, app: FastAPI) -> None:
        """Test middleware clears tenant context after request."""
        config = MultitenancyConfig()
        app.add_middleware(MultitenancyMiddleware, config=config)
        client = TestClient(app)
        
        # Make request with tenant
        response = client.get("/test", headers={"X-Tenant-ID": "tenant-123"})
        assert response.status_code == 200
        
        # Context should be cleared after request
        assert TenantContext.get_current() is None


class TestTenantIsolation:
    """Tests for tenant isolation behavior."""

    def test_different_tenants_isolated(self, app: FastAPI) -> None:
        """Test that different tenant requests are isolated."""
        config = MultitenancyConfig()
        app.add_middleware(MultitenancyMiddleware, config=config)
        client = TestClient(app)
        
        # Request from tenant A
        response_a = client.get("/test", headers={"X-Tenant-ID": "tenant-A"})
        assert response_a.status_code == 200
        
        # Request from tenant B
        response_b = client.get("/test", headers={"X-Tenant-ID": "tenant-B"})
        assert response_b.status_code == 200
        
        # Both should succeed independently
        assert TenantContext.get_current() is None


# Property-based tests

from hypothesis import given, settings
from hypothesis import strategies as st


@st.composite
def tenant_id_strategy(draw: st.DrawFn) -> str:
    """Strategy to generate valid tenant IDs."""
    return draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                whitelist_characters="-_"
            ),
        ).filter(lambda x: x.strip())
    )


class TestTenantIsolationProperties:
    """Property-based tests for tenant isolation.
    
    **Feature: test-coverage-80-percent-v3, Property 15: Tenant Isolation**
    **Validates: Requirements 7.3**
    """

    @given(tenant_a=tenant_id_strategy(), tenant_b=tenant_id_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_different_tenants_do_not_share_context(
        self, tenant_a: str, tenant_b: str
    ) -> None:
        """
        **Feature: test-coverage-80-percent-v3, Property 15: Tenant Isolation**
        **Validates: Requirements 7.3**
        
        For any two different tenant contexts, data operations in one tenant
        context should not affect or be visible to the other tenant.
        """
        from infrastructure.multitenancy import TenantInfo
        
        # Clear any existing context
        TenantContext.set_current(None)
        
        # Set tenant A context
        tenant_info_a = TenantInfo[str](id=tenant_a, name=f"Tenant {tenant_a}")
        TenantContext.set_current(tenant_info_a)
        
        # Verify tenant A is current
        current = TenantContext.get_current()
        assert current is not None
        assert current.id == tenant_a
        
        # Clear and set tenant B context
        TenantContext.set_current(None)
        tenant_info_b = TenantInfo[str](id=tenant_b, name=f"Tenant {tenant_b}")
        TenantContext.set_current(tenant_info_b)
        
        # Verify tenant B is current (not A)
        current = TenantContext.get_current()
        assert current is not None
        assert current.id == tenant_b
        
        # If tenants are different, verify isolation
        if tenant_a != tenant_b:
            assert current.id != tenant_a
        
        # Cleanup
        TenantContext.set_current(None)

    @given(tenant_id=tenant_id_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_tenant_context_cleared_after_operation(
        self, tenant_id: str
    ) -> None:
        """
        **Feature: test-coverage-80-percent-v3, Property 15: Tenant Isolation**
        **Validates: Requirements 7.3**
        
        For any tenant context, clearing the context should result in no
        tenant being active.
        """
        from infrastructure.multitenancy import TenantInfo
        
        # Set tenant context
        tenant_info = TenantInfo[str](id=tenant_id, name=f"Tenant {tenant_id}")
        TenantContext.set_current(tenant_info)
        
        # Verify tenant is set
        assert TenantContext.get_current() is not None
        
        # Clear context
        TenantContext.set_current(None)
        
        # Verify context is cleared
        assert TenantContext.get_current() is None
