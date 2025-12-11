"""multitenancy models."""

# Import at runtime to avoid circular dependency
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Self

# Context variable for current tenant
_current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)


def get_current_tenant() -> str | None:
    """Get the current tenant ID from context."""
    return _current_tenant.get()


def set_current_tenant(tenant_id: str | None) -> None:
    """Set the current tenant ID in context."""
    _current_tenant.set(tenant_id)


@dataclass(slots=True)
class TenantContext:
    """Context manager for tenant scope.

    Automatically sets and clears the tenant context.

    Usage:
        async with TenantContext("tenant_123"):
            # All operations use tenant_123
            items = await repo.get_all()
    """

    tenant_id: str
    _previous: str | None = None

    def __enter__(self) -> Self:
        """Enter tenant context."""
        self._previous = get_current_tenant()
        set_current_tenant(self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit tenant context and restore previous."""
        set_current_tenant(self._previous)

    async def __aenter__(self) -> Self:
        """Async enter tenant context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async exit tenant context."""
        self.__exit__(exc_type, exc_val, exc_tb)
