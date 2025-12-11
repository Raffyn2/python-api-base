"""Task queue endpoints.

**Feature: enterprise-generics-2025**
"""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from interface.v1.enterprise.dependencies import get_task_queue
from interface.v1.enterprise.models import (
    EmailTaskPayload,
    TaskEnqueueRequest,
    TaskEnqueueResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Task Queue"])


@router.post(
    "/tasks/enqueue",
    response_model=TaskEnqueueResponse,
    summary="Enqueue Task",
)
async def enqueue_task(request: TaskEnqueueRequest) -> TaskEnqueueResponse:
    """Enqueue email task."""
    try:
        queue = await get_task_queue()
    except Exception as e:
        logger.exception("task_queue_unavailable")
        raise HTTPException(
            status_code=503,
            detail="Task queue service unavailable",
        ) from e

    task = EmailTaskPayload(
        to=request.to,
        subject=request.subject,
        body=request.body,
    )

    handle = await queue.enqueue(task)

    logger.info(
        "task_enqueued",
        task_id=handle.task_id,
        task_type="email",
    )

    return TaskEnqueueResponse(
        task_id=handle.task_id,
        status="pending",
    )


@router.get("/tasks/{task_id}/status", summary="Get Task Status")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """Get task status."""
    try:
        queue = await get_task_queue()
    except Exception as e:
        logger.exception("task_queue_unavailable")
        raise HTTPException(
            status_code=503,
            detail="Task queue service unavailable",
        ) from e

    status = await queue.get_status(task_id)

    return {
        "task_id": task_id,
        "status": status.value,
    }
