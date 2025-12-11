"""Unit tests for multitenancy module.

Tests TenantResolutionStrategy, TenantInfo, TenantContext, SchemaConfig,
TenantSchemaManager, TenantScopedCache, and TenantAuditEntry.
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
        """Test HEADER value."""
        assert TenantResolutionStrategy.HEADER.value == "header"

    def test_subdomain_value(self) -> None:
        """Test SUBDOMAIN value."""
        assert TenantResolutionStrategy.SUBDOMAIN.value == "subdomain"

    def test_path_value(self) -> None:
        """Test PATH value."""
        assert TenantResolutionStrategy.PATH.value == "path"

    def test_jwt_claim_value(self) -> None:
        """Test JWT_CLAIM value."""
        assert TenantResolutionStrategy.JWT_CLAIM.value == "jwt_claim"

    def test_query_param_value(self) -> None:
        """Test QUERY_PARAM value."""
        assert TenantResolutionStrategy.QUERY_PARAM.value == "query_param"


class TestTenantInfo:
    """Tests for TenantInfo dataclass."""

    def test_creation(self) -> None:
        """Test TenantInfo creation."""
        tenant = TenantInfo[str](
            id="tenant-123",
            name="Acme Corp",
        )

        assert tenant.id == "tenant-123"
        assert tenant.name == "Acme Corp"
        assert tenant.schema_name is None
        assert tenant.settings is None
        assert tenant.is_active is True

    def test_creation_with_all_fields(self) -> None:
        """Test TenantInfo with all fields."""
        tenant = TenantInfo[str](
            id="tenant-456",
            name="Test Corp",
            schema_name="tenant_456",
            settings={"feature_x": True},
            is_active=False,
        )

        assert tenant.schema_name == "tenant_456"
        assert tenant.settings == {"feature_x": True}
        assert tenant.is_active is False

    def test_immutability(self) -> None:
        """Test TenantInfo is immutable."""
        tenant = TenantInfo[str](id="tenant-123", name="Test")

        with pytest.raises(AttributeError):
            tenant.name = "Other"  # type: ignore

    def test_with_int_id(self) -> None:
        """Test TenantInfo with integer ID."""
        tenant = TenantInfo[int](id=123, name="Test")

        assert tenant.id == 123


class TestTenantContext:
    """Tests for TenantContext."""

    def test_default_values(self) -> None:
        """Test default context values."""
        context = TenantContext[str]()

        assert context._strategy == TenantResolutionStrategy.HEADER
        assert context._header_name == "X-Tenant-ID"
        assert context._jwt_claim == "tenant_id"
        assert context._query_param == "tenant_id"

    def test_custom_values(self) -> None:
        """Test custom context values."""
        context = TenantContext[str](
            strategy=TenantResolutionStrategy.JWT_CLAIM,
            header_name="X-Custom-Tenant",
            jwt_claim="org_id",
            query_param="org",
        )

        assert context._strategy == TenantResolutionStrategy.JWT_CLAIM
        assert context._header_name == "X-Custom-Tenant"
        assert context._jwt_claim == "org_id"
        assert context._query_param == "org"

    def test_resolve_from_headers(self) -> None:
        """Test resolving tenant from headers."""
        context = TenantContext[str]()
        headers = {"X-Tenant-ID": "tenant-123"}

        result = context.resolve_from_headers(headers)

        assert result == "tenant-123"

    def test_resolve_from_headers_not_found(self) -> None:
        """Test resolving tenant from headers when not present."""
        context = TenantContext[str]()
        headers = {"Other-Header": "value"}

        result = context.resolve_from_headers(headers)

        assert result is None

    def test_resolve_from_jwt(self) -> None:
        """Test resolving tenant from JWT claims."""
        context = TenantContext[str]()
        claims = {"tenant_id": "tenant-456", "sub": "user-123"}

        result = context.resolve_from_jwt(claims)

        assert result == "tenant-456"

    def test_resolve_from_query(self) -> None:
        """Test resolving tenant from query params."""
        context = TenantContext[str]()
        params = {"tenant_id": "tenant-789"}

        result = context.resolve_from_query(params)

        assert result == "tenant-789"

    def test_get_set_current(self) -> None:
        """Test getting and setting current tenant."""
        tenant = TenantInfo[str](id="tenant-123", name="Test")

        TenantContext.set_current(tenant)
        result = TenantContext.get_current()

        assert result is not None
        assert result.id == "tenant-123"

        # Clean up
        TenantContext.set_current(None)

    def test_get_current_none(self) -> None:
        """Test getting current tenant when not set."""
        TenantContext.set_current(None)

        result = TenantContext.get_current()

        assert result is None


class TestSchemaConfig:
    """Tests for SchemaConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = SchemaConfig()

        assert config.default_schema == "public"
        assert config.schema_prefix == "tenant_"
        assert config.create_on_provision is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
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

    def test_get_schema_name(self) -> None:
        """Test getting schema name for tenant."""
        config = SchemaConfig(schema_prefix="tenant_")
        manager = TenantSchemaManager[str](config)

        result = manager.get_schema_name("acme")

        assert result == "tenant_acme"

    def test_get_schema_name_custom_prefix(self) -> None:
        """Test getting schema name with custom prefix."""
        config = SchemaConfig(schema_prefix="org_")
        manager = TenantSchemaManager[str](config)

        result = manager.get_schema_name("corp")

        assert result == "org_corp"

    def test_get_connection_schema_with_schema_name(self) -> None:
        """Test getting connection schema when tenant has schema_name."""
        config = SchemaConfig()
        manager = TenantSchemaManager[str](config)
        tenant = TenantInfo[str](
            id="tenant-123",
            name="Test",
            schema_name="custom_schema",
        )

        result = manager.get_connection_schema(tenant)

        assert result == "custom_schema"

    def test_get_connection_schema_without_schema_name(self) -> None:
        """Test getting connection schema when tenant has no schema_name."""
        config = SchemaConfig(schema_prefix="tenant_")
        manager = TenantSchemaManager[str](config)
        tenant = TenantInfo[str](id="acme", name="Acme")

        result = manager.get_connection_schema(tenant)

        assert result == "tenant_acme"


class TestTenantScopedCache:
    """Tests for TenantScopedCache."""

    def test_get_key(self) -> None:
        """Test getting tenant-scoped cache key."""
        cache = TenantScopedCache[str]()

        result = cache.get_key("tenant-123", "user:456")

        assert result == "tenant:tenant-123:user:456"

    def test_get_key_custom_prefix(self) -> None:
        """Test getting key with custom prefix."""
        cache = TenantScopedCache[str](prefix="org")

        result = cache.get_key("acme", "data:key")

        assert result == "org:acme:data:key"

    def test_get_pattern(self) -> None:
        """Test getting pattern for all tenant keys."""
        cache = TenantScopedCache[str]()

        result = cache.get_pattern("tenant-123")

        assert result == "tenant:tenant-123:*"


class TestTenantAuditEntry:
    """Tests for TenantAuditEntry dataclass."""

    def test_creation(self) -> None:
        """Test TenantAuditEntry creation."""
        entry = TenantAuditEntry[str](
            tenant_id="tenant-123",
            user_id="user-456",
            action="CREATE",
            resource_type="Order",
            resource_id="order-789",
            timestamp="2025-01-01T00:00:00Z",
        )

        assert entry.tenant_id == "tenant-123"
        assert entry.user_id == "user-456"
        assert entry.action == "CREATE"
        assert entry.resource_type == "Order"
        assert entry.resource_id == "order-789"
        assert entry.details is None

    def test_creation_with_details(self) -> None:
        """Test TenantAuditEntry with details."""
        entry = TenantAuditEntry[str](
            tenant_id="tenant-123",
            user_id="user-456",
            action="UPDATE",
            resource_type="User",
            resource_id="user-789",
            timestamp="2025-01-01T00:00:00Z",
            details={"changed_fields": ["name", "email"]},
        )

        assert entry.details == {"changed_fields": ["name", "email"]}

    def test_immutability(self) -> None:
        """Test TenantAuditEntry is immutable."""
        entry = TenantAuditEntry[str](
            tenant_id="tenant-123",
            user_id="user-456",
            action="CREATE",
            resource_type="Order",
            resource_id="order-789",
            timestamp="2025-01-01T00:00:00Z",
        )

        with pytest.raises(AttributeError):
            entry.action = "DELETE"  # type: ignore
