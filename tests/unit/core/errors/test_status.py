"""Tests for core/errors/status.py - Status enums."""

import pytest

from src.core.errors.status import (
    EntityStatus,
    OperationStatus,
    TaskStatus,
    UserStatus,
    ValidationStatus,
)


class TestOperationStatus:
    """Tests for OperationStatus enum."""

    def test_success_value(self):
        assert OperationStatus.SUCCESS.value == "success"

    def test_failed_value(self):
        assert OperationStatus.FAILED.value == "failed"

    def test_pending_value(self):
        assert OperationStatus.PENDING.value == "pending"

    def test_in_progress_value(self):
        assert OperationStatus.IN_PROGRESS.value == "in_progress"

    def test_cancelled_value(self):
        assert OperationStatus.CANCELLED.value == "cancelled"

    def test_timeout_value(self):
        assert OperationStatus.TIMEOUT.value == "timeout"

    def test_partial_value(self):
        assert OperationStatus.PARTIAL.value == "partial"

    def test_is_string_enum(self):
        assert isinstance(OperationStatus.SUCCESS, str)
        assert OperationStatus.SUCCESS == "success"

    def test_all_members_count(self):
        assert len(OperationStatus) == 7

    def test_from_string(self):
        assert OperationStatus("success") == OperationStatus.SUCCESS
        assert OperationStatus("failed") == OperationStatus.FAILED

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            OperationStatus("invalid")


class TestValidationStatus:
    """Tests for ValidationStatus enum."""

    def test_valid_value(self):
        assert ValidationStatus.VALID.value == "valid"

    def test_invalid_value(self):
        assert ValidationStatus.INVALID.value == "invalid"

    def test_warning_value(self):
        assert ValidationStatus.WARNING.value == "warning"

    def test_skipped_value(self):
        assert ValidationStatus.SKIPPED.value == "skipped"

    def test_is_string_enum(self):
        assert isinstance(ValidationStatus.VALID, str)
        assert ValidationStatus.VALID == "valid"

    def test_all_members_count(self):
        assert len(ValidationStatus) == 4

    def test_from_string(self):
        assert ValidationStatus("valid") == ValidationStatus.VALID
        assert ValidationStatus("invalid") == ValidationStatus.INVALID


class TestEntityStatus:
    """Tests for EntityStatus enum."""

    def test_active_value(self):
        assert EntityStatus.ACTIVE.value == "active"

    def test_inactive_value(self):
        assert EntityStatus.INACTIVE.value == "inactive"

    def test_pending_value(self):
        assert EntityStatus.PENDING.value == "pending"

    def test_suspended_value(self):
        assert EntityStatus.SUSPENDED.value == "suspended"

    def test_deleted_value(self):
        assert EntityStatus.DELETED.value == "deleted"

    def test_archived_value(self):
        assert EntityStatus.ARCHIVED.value == "archived"

    def test_is_string_enum(self):
        assert isinstance(EntityStatus.ACTIVE, str)
        assert EntityStatus.ACTIVE == "active"

    def test_all_members_count(self):
        assert len(EntityStatus) == 6

    def test_from_string(self):
        assert EntityStatus("active") == EntityStatus.ACTIVE
        assert EntityStatus("deleted") == EntityStatus.DELETED


class TestUserStatus:
    """Tests for UserStatus enum."""

    def test_active_value(self):
        assert UserStatus.ACTIVE.value == "active"

    def test_inactive_value(self):
        assert UserStatus.INACTIVE.value == "inactive"

    def test_pending_verification_value(self):
        assert UserStatus.PENDING_VERIFICATION.value == "pending_verification"

    def test_suspended_value(self):
        assert UserStatus.SUSPENDED.value == "suspended"

    def test_banned_value(self):
        assert UserStatus.BANNED.value == "banned"

    def test_deleted_value(self):
        assert UserStatus.DELETED.value == "deleted"

    def test_is_string_enum(self):
        assert isinstance(UserStatus.ACTIVE, str)
        assert UserStatus.ACTIVE == "active"

    def test_all_members_count(self):
        assert len(UserStatus) == 6

    def test_from_string(self):
        assert UserStatus("active") == UserStatus.ACTIVE
        assert UserStatus("banned") == UserStatus.BANNED


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_pending_value(self):
        assert TaskStatus.PENDING.value == "pending"

    def test_queued_value(self):
        assert TaskStatus.QUEUED.value == "queued"

    def test_running_value(self):
        assert TaskStatus.RUNNING.value == "running"

    def test_completed_value(self):
        assert TaskStatus.COMPLETED.value == "completed"

    def test_failed_value(self):
        assert TaskStatus.FAILED.value == "failed"

    def test_cancelled_value(self):
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_retrying_value(self):
        assert TaskStatus.RETRYING.value == "retrying"

    def test_is_string_enum(self):
        assert isinstance(TaskStatus.PENDING, str)
        assert TaskStatus.PENDING == "pending"

    def test_all_members_count(self):
        assert len(TaskStatus) == 7

    def test_from_string(self):
        assert TaskStatus("pending") == TaskStatus.PENDING
        assert TaskStatus("completed") == TaskStatus.COMPLETED


class TestStatusEnumComparisons:
    """Tests for comparing status enums."""

    def test_operation_status_equality(self):
        assert OperationStatus.SUCCESS == OperationStatus.SUCCESS
        assert OperationStatus.SUCCESS != OperationStatus.FAILED

    def test_validation_status_equality(self):
        assert ValidationStatus.VALID == ValidationStatus.VALID
        assert ValidationStatus.VALID != ValidationStatus.INVALID

    def test_entity_status_equality(self):
        assert EntityStatus.ACTIVE == EntityStatus.ACTIVE
        assert EntityStatus.ACTIVE != EntityStatus.INACTIVE

    def test_user_status_equality(self):
        assert UserStatus.ACTIVE == UserStatus.ACTIVE
        assert UserStatus.ACTIVE != UserStatus.BANNED

    def test_task_status_equality(self):
        assert TaskStatus.PENDING == TaskStatus.PENDING
        assert TaskStatus.PENDING != TaskStatus.COMPLETED

    def test_string_comparison(self):
        assert OperationStatus.SUCCESS == "success"
        assert ValidationStatus.VALID == "valid"
        assert EntityStatus.ACTIVE == "active"
        assert UserStatus.ACTIVE == "active"
        assert TaskStatus.PENDING == "pending"


class TestStatusEnumIteration:
    """Tests for iterating over status enums."""

    def test_operation_status_iteration(self):
        values = [s.value for s in OperationStatus]
        assert "success" in values
        assert "failed" in values
        assert "pending" in values

    def test_validation_status_iteration(self):
        values = [s.value for s in ValidationStatus]
        assert "valid" in values
        assert "invalid" in values

    def test_entity_status_iteration(self):
        values = [s.value for s in EntityStatus]
        assert "active" in values
        assert "deleted" in values

    def test_user_status_iteration(self):
        values = [s.value for s in UserStatus]
        assert "active" in values
        assert "banned" in values

    def test_task_status_iteration(self):
        values = [s.value for s in TaskStatus]
        assert "pending" in values
        assert "completed" in values


class TestStatusEnumMembership:
    """Tests for membership checks."""

    def test_operation_status_membership(self):
        assert "SUCCESS" in OperationStatus.__members__
        assert "FAILED" in OperationStatus.__members__

    def test_validation_status_membership(self):
        assert "VALID" in ValidationStatus.__members__
        assert "INVALID" in ValidationStatus.__members__

    def test_entity_status_membership(self):
        assert "ACTIVE" in EntityStatus.__members__
        assert "DELETED" in EntityStatus.__members__

    def test_user_status_membership(self):
        assert "ACTIVE" in UserStatus.__members__
        assert "BANNED" in UserStatus.__members__

    def test_task_status_membership(self):
        assert "PENDING" in TaskStatus.__members__
        assert "COMPLETED" in TaskStatus.__members__
