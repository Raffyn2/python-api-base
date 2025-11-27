"""Unit of Work pattern for transaction management."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Self

from sqlalchemy.ext.asyncio import AsyncSession


class IUnitOfWork(ABC):
    """Abstract Unit of Work interface.

    Coordinates the work of multiple repositories by maintaining
    a list of objects affected by a business transaction and
    coordinates the writing out of changes.
    """

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        ...


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """SQLAlchemy implementation of Unit of Work.

    Wraps database operations in a transaction that can be
    committed or rolled back atomically.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize Unit of Work.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    @property
    def session(self) -> AsyncSession:
        """Get the underlying session."""
        return self._session

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager, rolling back on error."""
        if exc_type is not None:
            await self.rollback()
        await self._session.close()


@asynccontextmanager
async def transaction(uow: IUnitOfWork) -> AsyncGenerator[IUnitOfWork, None]:
    """Context manager for transactional operations.

    Usage:
        async with transaction(uow) as unit:
            await repo.create(entity)
            await repo.update(other_entity)
        # Auto-commits on success, rollbacks on error

    Args:
        uow: Unit of Work instance.

    Yields:
        The Unit of Work for use in the transaction.
    """
    try:
        yield uow
        await uow.commit()
    except Exception:
        await uow.rollback()
        raise
