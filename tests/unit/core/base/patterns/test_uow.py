"""Tests for core/base/patterns/uow.py - Unit of Work pattern."""

from typing import Any, Self

import pytest

from src.core.base.patterns.uow import UnitOfWork


class ConcreteUnitOfWork(UnitOfWork):
    """Concrete implementation for testing."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.flushed = False
        self.entered = False
        self.exited = False
        self.exit_exception = None

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.exited = True
        self.exit_exception = exc_val
        if exc_val is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def flush(self) -> None:
        self.flushed = True


class TestUnitOfWorkInterface:
    """Tests for UnitOfWork abstract interface."""

    def test_is_abstract_class(self):
        with pytest.raises(TypeError):
            UnitOfWork()

    def test_has_aenter_method(self):
        assert hasattr(UnitOfWork, "__aenter__")

    def test_has_aexit_method(self):
        assert hasattr(UnitOfWork, "__aexit__")

    def test_has_commit_method(self):
        assert hasattr(UnitOfWork, "commit")

    def test_has_rollback_method(self):
        assert hasattr(UnitOfWork, "rollback")

    def test_has_flush_method(self):
        assert hasattr(UnitOfWork, "flush")


class TestConcreteUnitOfWork:
    """Tests for concrete UnitOfWork implementation."""

    @pytest.mark.asyncio
    async def test_context_manager_enter(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            assert uow.entered is True

    @pytest.mark.asyncio
    async def test_context_manager_exit(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            pass
        assert uow.exited is True

    @pytest.mark.asyncio
    async def test_commit(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            await uow.commit()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_rollback(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            await uow.rollback()
        assert uow.rolled_back is True

    @pytest.mark.asyncio
    async def test_flush(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            await uow.flush()
        assert uow.flushed is True

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self):
        uow = ConcreteUnitOfWork()
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test error")
        assert uow.rolled_back is True

    @pytest.mark.asyncio
    async def test_exit_receives_exception(self):
        uow = ConcreteUnitOfWork()
        error = ValueError("Test error")
        with pytest.raises(ValueError):
            async with uow:
                raise error
        assert uow.exit_exception is error


class TestUnitOfWorkUsagePatterns:
    """Tests for common UoW usage patterns."""

    @pytest.mark.asyncio
    async def test_commit_after_operations(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            # Simulate operations
            await uow.flush()
            await uow.commit()
        assert uow.flushed is True
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_no_commit_without_explicit_call(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            pass
        assert uow.committed is False

    @pytest.mark.asyncio
    async def test_multiple_flushes(self):
        uow = ConcreteUnitOfWork()
        async with uow:
            await uow.flush()
            await uow.flush()
            await uow.commit()
        assert uow.flushed is True
        assert uow.committed is True
