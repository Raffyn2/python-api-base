"""Unit tests for multitenancy tenant module.

**Feature: test-coverage-80-percent-v3**
**Validates: Requirements 7.3**
"""

from infrastructure.multitenancy.tenant import (
    SchemaConfig,
    TenantContext,
    TenantInfo,
    TenantSchemaManager,
    TenantScopedCache,
)


class TestTenantInfo:
    """Tests for TenantInfo dataclass."""

    def test_create_tenant_info(self) -> None:
        """Test creating tenant info."""
        tenant = TenantInfo[str](
            id="tenant-1",
            name="Test Tenant",
        )
        assert tenant.id == "tenant-1"
        assert tenant.name == "Test Tenant"
        assert tenant.is_active is True

    def test_tenant_info_with_schema(self) -> None:
        """Test tenant info with schema."""
        tenant = TenantInfo[str](
            id="tenant-1",
            name="Test",
            schema_name="tenant_schema",
        )
        assert tenant.schema_name == "tenant_schema"

    def test_tenant_info_with_settings(self) -> None:
        """Test tenant info with settings."""
        tenant = TenantInfo[str](
            id="tenant-1",
            name="Test",
            settings={"max_users": 100},
        )
        assert tenant.settings["max_users"] == 100


class TestTenantContext:
    """Tests for TenantContext."""

    def test_get_set_clear_tenant(self) -> None:
        """Test tenant context operations."""
        tenant = TenantInfo[str](id="t1", name="Test")

        # Initially None
        TenantContext.set_current(None)
        assert TenantContext.get_current() is None

        # Set tenant
        TenantContext.set_current(tenant)
        assert TenantContext.get_current() == tenant

        # Clear tenant
        TenantContext.set_current(None)
        assert TenantContext.get_current() is None

    def test_resolve_from_headers(self) -> None:
        """Test resolving tenant from headers."""
        context = TenantContext[str]()
        headers = {"X-Tenant-ID": "tenant-123"}

        tenant_id = context.resolve_from_headers(headers)

        assert tenant_id == "tenant-123"

    def test_resolve_from_jwt(self) -> None:
        """Test resolving tenant from JWT claims."""
        context = TenantContext[str]()
        claims = {"tenant_id": "tenant-456"}

        tenant_id = context.resolve_from_jwt(claims)

        assert tenant_id == "tenant-456"

    def test_resolve_from_query(self) -> None:
        """Test resolving tenant from query params."""
        context = TenantContext[str]()
        params = {"tenant_id": "tenant-789"}

        tenant_id = context.resolve_from_query(params)

        assert tenant_id == "tenant-789"


class TestTenantSchemaManager:
    """Tests for TenantSchemaManager."""

    def test_get_schema_name(self) -> None:
        """Test getting schema name for tenant."""
        config = SchemaConfig()
        manager = TenantSchemaManager[str](config)

        schema = manager.get_schema_name("tenant-1")

        assert schema == "tenant_tenant-1"

    def test_get_connection_schema_with_custom(self) -> None:
        """Test getting connection schema with custom schema."""
        config = SchemaConfig()
        manager = TenantSchemaManager[str](config)
        tenant = TenantInfo[str](id="t1", name="Test", schema_name="custom_schema")

        schema = manager.get_connection_schema(tenant)

        assert schema == "custom_schema"


class TestTenantScopedCache:
    """Tests for TenantScopedCache."""

    def test_get_key(self) -> None:
        """Test getting tenant-scoped cache key."""
        cache = TenantScopedCache[str]()

        key = cache.get_key("tenant-1", "user:123")

        assert key == "tenant:tenant-1:user:123"

    def test_get_pattern(self) -> None:
        """Test getting pattern for tenant keys."""
        cache = TenantScopedCache[str]()

        pattern = cache.get_pattern("tenant-1")

        assert pattern == "tenant:tenant-1:*"
