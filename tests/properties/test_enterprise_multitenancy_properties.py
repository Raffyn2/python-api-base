"""Property-based tests for multi-tenancy.

**Feature: enterprise-features-2025, Tasks 4.2, 4.3, 4.5, 4.7**
**Validates: Requirements 4.2, 4.3, 4.5, 4.7, 4.9**
"""

import asyncio
import contextvars
from dataclasses import dataclass

import pytest
from hypothesis import given, settings, strategies as st

# Tenant context using contextvars
_current_tenant: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_tenant", default=None)


def get_current_tenant() -> str | None:
    """Get current tenant from context."""
    return _current_tenant.get()


def set_current_tenant(tenant_id: str | None) -> contextvars.Token[str | None]:
    """Set current tenant in context."""
    return _current_tenant.set(tenant_id)


@dataclass
class TenantAwareEntity:
    """Test entity with tenant awareness."""

    id: str
    tenant_id: str
    data: str


class TenantRepository[T]:
    """Simple tenant-aware repository for testing."""

    def __init__(self) -> None:
        self._storage: dict[str, T] = {}

    def _get_tenant(self) -> str:
        """Get current tenant or raise."""
        tenant = get_current_tenant()
        if tenant is None:
            raise PermissionError("No tenant context")
        return tenant

    async def save(self, entity: TenantAwareEntity) -> TenantAwareEntity:
        """Save entity with tenant tagging."""
        tenant = self._get_tenant()
        # Auto-set tenant_id
        tagged = TenantAwareEntity(
            id=entity.id,
            tenant_id=tenant,
            data=entity.data,
        )
        self._storage[f"{tenant}:{entity.id}"] = tagged  # type: ignore
        return tagged

    async def find_by_id(self, entity_id: str) -> TenantAwareEntity | None:
        """Find entity filtered by current tenant."""
        tenant = self._get_tenant()
        return self._storage.get(f"{tenant}:{entity_id}")  # type: ignore

    async def find_all(self) -> list[TenantAwareEntity]:
        """Find all entities for current tenant."""
        tenant = self._get_tenant()
        prefix = f"{tenant}:"
        return [v for k, v in self._storage.items() if k.startswith(prefix)]  # type: ignore

    async def cross_tenant_access(self, entity_id: str, target_tenant: str) -> TenantAwareEntity | None:
        """Attempt cross-tenant access (should be blocked)."""
        current = self._get_tenant()
        if target_tenant != current:
            raise PermissionError(f"Cross-tenant access denied: {current} -> {target_tenant}")
        return self._storage.get(f"{target_tenant}:{entity_id}")  # type: ignore


# Strategies
tenant_ids = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=20,
)
entity_ids = st.uuids().map(str)
data_values = st.text(min_size=1, max_size=100)


class TestTenantQueryFiltering:
    """**Feature: enterprise-features-2025, Property 10: Tenant Isolation - Query Filtering**
    **Validates: Requirements 4.2**
    """

    @given(
        tenant1=tenant_ids,
        tenant2=tenant_ids,
        entity_id=entity_ids,
        data=data_values,
    )
    @settings(max_examples=50)
    def test_query_only_returns_current_tenant_data(
        self, tenant1: str, tenant2: str, entity_id: str, data: str
    ) -> None:
        """Queries only return data belonging to current tenant."""
        if tenant1 == tenant2:
            return  # Skip if same tenant

        async def run_test() -> None:
            repo: TenantRepository[TenantAwareEntity] = TenantRepository()

            # Save entity as tenant1
            token1 = set_current_tenant(tenant1)
            entity = TenantAwareEntity(id=entity_id, tenant_id="", data=data)
            await repo.save(entity)
            _current_tenant.reset(token1)

            # Query as tenant2 - should not find it
            token2 = set_current_tenant(tenant2)
            result = await repo.find_by_id(entity_id)
            assert result is None

            all_results = await repo.find_all()
            assert len(all_results) == 0
            _current_tenant.reset(token2)

        asyncio.run(run_test())


class TestTenantInsertTagging:
    """**Feature: enterprise-features-2025, Property 11: Tenant Isolation - Insert Tagging**
    **Validates: Requirements 4.3**
    """

    @given(
        tenant_id=tenant_ids,
        entity_id=entity_ids,
        data=data_values,
    )
    @settings(max_examples=50)
    def test_insert_auto_tags_tenant(self, tenant_id: str, entity_id: str, data: str) -> None:
        """Inserted entities are automatically tagged with current tenant."""

        async def run_test() -> None:
            repo: TenantRepository[TenantAwareEntity] = TenantRepository()

            token = set_current_tenant(tenant_id)
            entity = TenantAwareEntity(id=entity_id, tenant_id="wrong", data=data)
            saved = await repo.save(entity)

            # Tenant should be auto-set to current
            assert saved.tenant_id == tenant_id
            _current_tenant.reset(token)

        asyncio.run(run_test())


class TestCrossTenantBlocking:
    """**Feature: enterprise-features-2025, Property 12: Tenant Isolation - Cross-Tenant Block**
    **Validates: Requirements 4.5, 4.7**
    """

    @given(
        tenant1=tenant_ids,
        tenant2=tenant_ids,
        entity_id=entity_ids,
    )
    @settings(max_examples=50)
    def test_cross_tenant_access_blocked(self, tenant1: str, tenant2: str, entity_id: str) -> None:
        """Cross-tenant access attempts are blocked."""
        if tenant1 == tenant2:
            return  # Skip if same tenant

        async def run_test() -> None:
            repo: TenantRepository[TenantAwareEntity] = TenantRepository()

            token = set_current_tenant(tenant1)

            with pytest.raises(PermissionError) as exc_info:
                await repo.cross_tenant_access(entity_id, tenant2)

            assert "Cross-tenant access denied" in str(exc_info.value)
            _current_tenant.reset(token)

        asyncio.run(run_test())


class TestTenantContextPropagation:
    """**Feature: enterprise-features-2025, Property 23: Tenant Context Propagation**
    **Validates: Requirements 4.9**
    """

    @given(tenant_id=tenant_ids)
    @settings(max_examples=50)
    def test_context_propagates_in_async(self, tenant_id: str) -> None:
        """Tenant context propagates correctly in async operations."""

        async def inner_operation() -> str | None:
            return get_current_tenant()

        async def run_test() -> None:
            token = set_current_tenant(tenant_id)

            # Context should be available in nested async
            result = await inner_operation()
            assert result == tenant_id

            _current_tenant.reset(token)

        asyncio.run(run_test())

    @given(tenant_id=tenant_ids)
    @settings(max_examples=30)
    def test_context_isolated_between_tasks(self, tenant_id: str) -> None:
        """Tenant context is isolated between concurrent tasks."""

        async def task_with_tenant(tid: str) -> str | None:
            set_current_tenant(tid)
            await asyncio.sleep(0.001)  # Yield to other tasks
            return get_current_tenant()

        async def run_test() -> None:
            # Run multiple tasks with different tenants
            results = await asyncio.gather(
                task_with_tenant(tenant_id),
                task_with_tenant(f"{tenant_id}_other"),
            )

            # Each task should see its own tenant
            assert results[0] == tenant_id
            assert results[1] == f"{tenant_id}_other"

        asyncio.run(run_test())
