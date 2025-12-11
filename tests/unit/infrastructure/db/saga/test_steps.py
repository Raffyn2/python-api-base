"""Tests for saga steps module.

**Feature: realistic-test-coverage**
**Validates: Requirements 3.1**
"""

from datetime import UTC, datetime

import pytest

from infrastructure.db.saga.context import SagaContext
from infrastructure.db.saga.enums import StepStatus
from infrastructure.db.saga.steps import SagaStep, StepResult


class TestSagaStep:
    """Tests for SagaStep."""

    @pytest.mark.asyncio
    async def test_create_step(self) -> None:
        """Test creating a saga step."""

        async def action(ctx: SagaContext) -> None:
            pass

        step = SagaStep(name="create_order", action=action)
        assert step.name == "create_order"
        assert step.status == StepStatus.PENDING

    @pytest.mark.asyncio
    async def test_step_with_compensation(self) -> None:
        """Test step with compensation action."""

        async def action(ctx: SagaContext) -> None:
            pass

        async def compensate(ctx: SagaContext) -> None:
            pass

        step = SagaStep(
            name="create_order",
            action=action,
            compensation=compensate,
        )
        assert step.compensation is not None

    @pytest.mark.asyncio
    async def test_step_with_timeout(self) -> None:
        """Test step with timeout."""

        async def action(ctx: SagaContext) -> None:
            pass

        step = SagaStep(
            name="create_order",
            action=action,
            timeout_seconds=30.0,
        )
        assert step.timeout_seconds == 30.0

    def test_default_timeout_is_none(self) -> None:
        """Test default timeout is None."""

        async def action(ctx: SagaContext) -> None:
            pass

        step = SagaStep(name="test", action=action)
        assert step.timeout_seconds is None

    def test_default_error_is_none(self) -> None:
        """Test default error is None."""

        async def action(ctx: SagaContext) -> None:
            pass

        step = SagaStep(name="test", action=action)
        assert step.error is None

    def test_default_timestamps_are_none(self) -> None:
        """Test default timestamps are None."""

        async def action(ctx: SagaContext) -> None:
            pass

        step = SagaStep(name="test", action=action)
        assert step.started_at is None
        assert step.completed_at is None

    def test_reset(self) -> None:
        """Test resetting step to initial state."""

        async def action(ctx: SagaContext) -> None:
            pass

        step = SagaStep(name="test", action=action)
        step.status = StepStatus.COMPLETED
        step.error = Exception("test error")
        step.started_at = datetime.now(UTC)
        step.completed_at = datetime.now(UTC)

        step.reset()

        assert step.status == StepStatus.PENDING
        assert step.error is None
        assert step.started_at is None
        assert step.completed_at is None


class TestStepResult:
    """Tests for StepResult."""

    def test_create_result(self) -> None:
        """Test creating step result."""
        result = StepResult(
            step_name="create_order",
            status=StepStatus.COMPLETED,
        )
        assert result.step_name == "create_order"
        assert result.status == StepStatus.COMPLETED

    def test_result_with_error(self) -> None:
        """Test result with error."""
        error = ValueError("Something went wrong")
        result = StepResult(
            step_name="create_order",
            status=StepStatus.FAILED,
            error=error,
        )
        assert result.error is error

    def test_result_with_duration(self) -> None:
        """Test result with duration."""
        result = StepResult(
            step_name="create_order",
            status=StepStatus.COMPLETED,
            duration_ms=150.5,
        )
        assert result.duration_ms == 150.5

    def test_default_error_is_none(self) -> None:
        """Test default error is None."""
        result = StepResult(
            step_name="test",
            status=StepStatus.COMPLETED,
        )
        assert result.error is None

    def test_default_duration_is_zero(self) -> None:
        """Test default duration is 0."""
        result = StepResult(
            step_name="test",
            status=StepStatus.COMPLETED,
        )
        assert result.duration_ms == 0.0
