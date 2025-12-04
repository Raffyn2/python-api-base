"""Saga Pattern for distributed transactions.

Provides orchestration-based saga implementation for managing
distributed transactions with automatic compensation (rollback).

**Feature: code-review-refactoring, Task 3.8: Create __init__.py with re-exports**
**Validates: Requirements 1.2, 3.5**

Original: saga.py (493 lines)
Refactored: saga/ package (7 files, ~40-180 lines each)

Usage:
    from infrastructure.db.saga import Saga, SagaStep, SagaBuilder

    saga = (
        SagaBuilder("create-order")
        .step("create_order", create_order, compensate_order)
        .step("reserve_inventory", reserve_inventory, release_inventory)
        .build()
    )

    result = await saga.execute({"order": order_data})
"""

# Backward compatible re-exports
from infrastructure.db.saga.builder import SagaBuilder
from infrastructure.db.saga.context import SagaContext
from infrastructure.db.saga.enums import SagaStatus, StepStatus
from infrastructure.db.saga.manager import SagaOrchestrator
from infrastructure.db.saga.orchestrator import Saga, SagaResult
from infrastructure.db.saga.steps import (
    CompensationAction,
    SagaStep,
    StepAction,
    StepResult,
)

__all__ = [
    "CompensationAction",
    # Orchestrator
    "Saga",
    # Builder
    "SagaBuilder",
    # Context
    "SagaContext",
    # Manager
    "SagaOrchestrator",
    "SagaResult",
    # Enums
    "SagaStatus",
    # Steps
    "SagaStep",
    "StepAction",
    "StepResult",
    "StepStatus",
]
