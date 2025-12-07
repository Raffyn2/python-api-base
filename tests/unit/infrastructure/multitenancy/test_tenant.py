"""Unit tests for multitenancy module.

Tests TenantInfo, TenantContext, TenantSchemaManager, and TenantScopedCache.
"""

import pytest

from infrastructure.multitenancy.tenant import (
    SchemaConfig,
    TenantAuditEntry,
    TenantContext,
    TenantInfo,
    TenantResolutionStrategy,
    TenantSchemaManager,
    TenantScopedCache,
)


class TestTenantResolutionStrategy:
    """Tests for TenantResolutionStrategy enum."""

    def test_header_value(self) -> None:
        """Test HEADER strategy value."""
        assert TenantResolutionStrategy.HEADER.value == "header"

    def test_subdomain_value(self) -> None:
        """Test SUBDOMAIN strategy value."""
        assert TenantResolutionStrategy.SUBDOMAIN.value == "subdomain"

    def test_path_value(self) -> None:
        """Test PATH strategy value."""
        assert TenantResolutionStrategy.PATH.value == "path"

    def test_jwt_claim_value(self) -> None:
        """Test JWT_CLAIM strategy value."""
        assert TenantResolutionStrategy.JWT_CLAIM.value == "jwt_claim"

    def test_query_param_value(self) -> None:
        """Test QUERY_PARAM strategy value."""
        assert TenantResolutionStrategy.QUERY_PARAM.value == "query_param"


class TestTenantInfo:
    """Tests for TenantInfo dataclass."""

    def test_basic_creation(self) -> None:
        """Test basic tenant info creation."""
        tenant: TenantInfo[str] = TenantInfo(
            id="tenant-123",
            name="Acme Corp",
        )
        assert tenant.id == "tenant-123"
        assert tenant.name == "Acme Corp"
        assert tenant.schema_name is None
        assert tenant.settings is None
        assert tenant.is_active is True

    def test_with_schema(self) -> None:
        """Test tenant info with schema."""
        tenant: TenantInfo[str] = TenantInfo(
            id="tenant-456",
            name="Test Corp",
            schema_name="tenant_456",
        )
        assert tenant.schema_name == "tenant_456"

    def test_with_settings(self) -> None:
        """Test tenant info with settings."""
        tenant: TenantInfo[str] = TenantInfo(
            id="tenant-789",
            name="Settings Corp",
            settings={"feature_x": True, "max_users": 100},
        )
        assert tenant.settings is not None
        assert tenant.settings["feature_x"] is True
        assert tenant.settings["max_users"] == 100

    def test_inactive_tenant(self) -> None:
        """Test inactive tenant."""
        tenant: TenantInfo[str] = TenantInfo(
            id="tenant-inactive",
            name="Inactive Corp",
            is_active=False,
        )
        assert tenant.is_active is False

    def test_frozen(self) -> None:
        """Test tenant info is immutable."""
        tenant: TenantInfo[str] = TenantInfo(id="t1", name="Test")
        with pytest.raises(AttributeError):
            tenant.name = "Changed"  # type: ignore[misc]

    def test_int_id(self) -> None:
        """Test tenant with integer ID."""
        tenant: TenantInfo[int] = TenantInfo(id=123, name="Int Tenant")
        assert tenant.id == 123


class TestTenantContext:
    """Tests for TenantContext."""

    def setup_method(self) -> None:
        """Clear tenant context before each test."""
        TenantContext.set_current(None)

    def teardown_method(self) -> None:
        """Clear tenant context after each test."""
        TenantContext.set_current(None)

    def test_default_strategy(self) -> None:
        """Test default resolution strategy."""
        ctx: TenantContext[str] = TenantContext()
        assert ctx._strategy == TenantResolutionStrategy.HEADER

    def test_custom_strategy(self) -> None:
        """Test custom resolution strategy."""
        ctx: TenantContext[str] = TenantContext(
            strategy=TenantResolutionStrategy.JWT_CLAIM
        )
        assert ctx._strategy == TenantResolutionStrategy.JWT_CLAIM

    def test_get_current_none(self) -> None:
        """Test get_current returns None when not set."""
        assert TenantContext.get_current() is None

    def test_set_and_get_current(self) -> None:
        """Test setting and getting current tenant."""
        tenant: TenantInfo[str] = TenantInfo(id="t1", name="Test")
        TenantContext.set_current(tenant)
        current = TenantContext.get_current()
        assert current is not None
        assert current.id == "t1"

    def test_resolve_from_headers(self) -> None:
        """Test resolving tenant from headers."""
        ctx: TenantContext[str] = TenantContext(header_name="X-Tenant-ID")
        headers = {"X-Tenant-ID": "tenant-from-header"}
        tenant_id = ctx.resolve_from_headers(headers)
        assert tenant_id == "tenant-from-header"

    def test_resolve_from_headers_missing(self) -> None:
        """Test resolving tenant from headers when missing."""
        ctx: TenantContext[str] = TenantContext()
        headers: dict[str, str] = {}
        tenant_id = ctx.resolve_from_headers(headers)
        assert tenant_id is None

    def test_resolve_from_jwt(self) -> None:
        """Test resolving tenant from JWT claims."""
        ctx: TenantContext[str] = TenantContext(jwt_claim="tenant_id")
        claims = {"tenant_id": "tenant-from-jwt", "sub": "user-123"}
        tenant_id = ctx.resolve_from_jwt(claims)
        assert tenant_id == "tenant-from-jwt"

    def test_resolve_from_query(self) -> None:
        """Test resolving tenant from query params."""
        ctx: TenantContext[str] = TenantContext(query_param="tenant")
        params = {"tenant": "tenant-from-query"}
        tenant_id = ctx.resolve_from_query(params)
        assert tenant_id == "tenant-from-query"


class TestSchemaConfig:
    """Tests for SchemaConfig."""

    def test_default_values(self) -> None:
        """Test default schema config values."""
        config = SchemaConfig()
        assert config.default_schema == "public"
        assert config.schema_prefix == "tenant_"
        assert config.create_on_provision is True

    def test_custom_values(self) -> None:
        """Test custom schema config values."""
        config = SchemaConfig(
            default_schema="main",
            schema_prefix="org_",
            create_on_provision=False,
        )
        assert config.default_schema == "main"
        assert config.schema_prefix == "org_"
        assert config.create_on_provision is False


class TestTenantSchemaManager:
    """Tests for TenantSchemaManager."""

    @pytest.fixture
    def manager(self) -> TenantSchemaManager[str]:
        """Create test schema manager."""
        config = SchemaConfig(schema_prefix="tenant_")
        return TenantSchemaManager(config)

    def test_get_schema_name(self, manager: TenantSchemaManager[str]) -> None:
        """Test getting schema name for tenant."""
        schema = manager.get_schema_name("acme")
        assert schema == "tenant_acme"

    def test_get_connection_schema_with_custom(
        self, manager: TenantSchemaManager[str]
    ) -> None:
        """Test getting connection schema with custom schema name."""
        tenant: TenantInfo[str] = TenantInfo(
            id="acme",
            name="Acme",
            schema_name="custom_schema",
        )
        schema = manager.get_connection_schema(tenant)
        assert schema == "custom_schema"

    def test_get_connection_schema_default(
        self, manager: TenantSchemaManager[str]
    ) -> None:
        """Test getting connection schema without custom schema."""
        tenant: TenantInfo[str] = TenantInfo(id="acme", name="Acme")
        schema = manager.get_connection_schema(tenant)
        assert schema == "tenant_acme"


class TestTenantScopedCache:
    """Tests for TenantScopedCache."""

    def test_default_prefix(self) -> None:
        """Test default cache prefix."""
        cache: TenantScopedCache[str] = TenantScopedCache()
        key = cache.get_key("tenant-1", "users:list")
        assert key == "tenant:tenant-1:users:list"

    def test_custom_prefix(self) -> None:
        """Test custom cache prefix."""
        cache: TenantScopedCache[str] = TenantScopedCache(prefix="org")
        key = cache.get_key("acme", "settings")
        assert key == "org:acme:settings"

    def test_get_pattern(self) -> None:
        """Test getting pattern for tenant keys."""
        cache: TenantScopedCache[str] = TenantScopedCache()
        pattern = cache.get_pattern("tenant-1")
        assert pattern == "tenant:tenant-1:*"

    def test_int_tenant_id(self) -> None:
        """Test with integer tenant ID."""
        cache: TenantScopedCache[int] = TenantScopedCache()
        key = cache.get_key(123, "data")
        assert key == "tenant:123:data"


class TestTenantAuditEntry:
    """Tests for TenantAuditEntry."""

    def test_basic_creation(self) -> None:
        """Test basic audit entry creation."""
        entry: TenantAuditEntry[str] = TenantAuditEntry(
            tenant_id="tenant-1",
            user_id="user-123",
            action="CREATE",
            resource_type="User",
            resource_id="user-456",
            timestamp="2025-01-01T00:00:00Z",
        )
        assert entry.tenant_id == "tenant-1"
        assert entry.user_id == "user-123"
        assert entry.action == "CREATE"
        assert entry.resource_type == "User"
        assert entry.details is None

    def test_with_details(self) -> None:
        """Test audit entry with details."""
        entry: TenantAuditEntry[str] = TenantAuditEntry(
            tenant_id="tenant-1",
            user_id="user-123",
            action="UPDATE",
            resource_type="Settings",
            resource_id="settings-1",
            timestamp="2025-01-01T00:00:00Z",
            details={"changed_fields": ["name", "email"]},
        )
        assert entry.details is not None
        assert "changed_fields" in entry.details

    def test_frozen(self) -> None:
        """Test audit entry is immutable."""
        entry: TenantAuditEntry[str] = TenantAuditEntry(
            tenant_id="t1",
            user_id="u1",
            action="DELETE",
            resource_type="Item",
            resource_id="i1",
            timestamp="2025-01-01T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            entry.action = "UPDATE"  # type: ignore[misc]
