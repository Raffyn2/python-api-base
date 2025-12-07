"""Tests for infrastructure/db/saga/enums.py - Saga status enums."""

import pytest

from src.infrastructure.db.saga.enums import SagaStatus, StepStatus


class TestSagaStatus:
    """Tests for SagaStatus enum."""

    def test_pending_value(self):
        assert SagaStatus.PENDING.value == "pending"

    def test_running_value(self):
        assert SagaStatus.RUNNING.value == "running"

    def test_completed_value(self):
        assert SagaStatus.COMPLETED.value == "completed"

    def test_compensating_value(self):
        assert SagaStatus.COMPENSATING.value == "compensating"

    def test_compensated_value(self):
        assert SagaStatus.COMPENSATED.value == "compensated"

    def test_failed_value(self):
        assert SagaStatus.FAILED.value == "failed"

    def test_is_string_enum(self):
        assert isinstance(SagaStatus.PENDING, str)
        assert SagaStatus.PENDING == "pending"

    def test_all_members_count(self):
        assert len(SagaStatus) == 6

    def test_from_string(self):
        assert SagaStatus("pending") == SagaStatus.PENDING
        assert SagaStatus("completed") == SagaStatus.COMPLETED

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            SagaStatus("invalid")


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_pending_value(self):
        assert StepStatus.PENDING.value == "pending"

    def test_running_value(self):
        assert StepStatus.RUNNING.value == "running"

    def test_completed_value(self):
        assert StepStatus.COMPLETED.value == "completed"

    def test_compensating_value(self):
        assert StepStatus.COMPENSATING.value == "compensating"

    def test_compensated_value(self):
        assert StepStatus.COMPENSATED.value == "compensated"

    def test_failed_value(self):
        assert StepStatus.FAILED.value == "failed"

    def test_skipped_value(self):
        assert StepStatus.SKIPPED.value == "skipped"

    def test_is_string_enum(self):
        assert isinstance(StepStatus.PENDING, str)
        assert StepStatus.PENDING == "pending"

    def test_all_members_count(self):
        assert len(StepStatus) == 7

    def test_from_string(self):
        assert StepStatus("pending") == StepStatus.PENDING
        assert StepStatus("skipped") == StepStatus.SKIPPED

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            StepStatus("invalid")


class TestSagaStatusTransitions:
    """Tests for saga status transitions."""

    def test_initial_status_is_pending(self):
        initial = SagaStatus.PENDING
        assert initial == "pending"

    def test_pending_to_running(self):
        status = SagaStatus.PENDING
        next_status = SagaStatus.RUNNING
        assert status != next_status

    def test_running_to_completed(self):
        status = SagaStatus.RUNNING
        next_status = SagaStatus.COMPLETED
        assert status != next_status

    def test_running_to_compensating(self):
        status = SagaStatus.RUNNING
        next_status = SagaStatus.COMPENSATING
        assert status != next_status

    def test_compensating_to_compensated(self):
        status = SagaStatus.COMPENSATING
        next_status = SagaStatus.COMPENSATED
        assert status != next_status


class TestStepStatusTransitions:
    """Tests for step status transitions."""

    def test_initial_status_is_pending(self):
        initial = StepStatus.PENDING
        assert initial == "pending"

    def test_step_can_be_skipped(self):
        status = StepStatus.SKIPPED
        assert status == "skipped"

    def test_step_status_has_more_states_than_saga(self):
        assert len(StepStatus) > len(SagaStatus)


class TestEnumComparisons:
    """Tests for enum comparisons."""

    def test_saga_status_equality(self):
        assert SagaStatus.PENDING == SagaStatus.PENDING
        assert SagaStatus.PENDING != SagaStatus.RUNNING

    def test_step_status_equality(self):
        assert StepStatus.PENDING == StepStatus.PENDING
        assert StepStatus.PENDING != StepStatus.RUNNING

    def test_string_comparison(self):
        assert SagaStatus.PENDING == "pending"
        assert StepStatus.SKIPPED == "skipped"

    def test_membership_check(self):
        assert "PENDING" in SagaStatus.__members__
        assert "SKIPPED" in StepStatus.__members__
        assert "SKIPPED" not in SagaStatus.__members__
