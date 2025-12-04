"""Contract tests for Health API.

Verifies the Health API contract for monitoring systems.

**Feature: contract-testing**
**Validates: Requirements 12.1, 12.3**
"""

import pytest
from pydantic import BaseModel, Field


class HealthResponseContract(BaseModel):
    """Expected contract for health check response."""

    status: str = Field(..., pattern=r"^(healthy|unhealthy|degraded)$")
    version: str
    timestamp: str


class ReadinessResponseContract(BaseModel):
    """Expected contract for readiness check response."""

    status: str = Field(..., pattern=r"^(ready|not_ready)$")
    checks: dict[str, bool] | None = None


class LivenessResponseContract(BaseModel):
    """Expected contract for liveness check response."""

    status: str = Field(..., pattern=r"^(alive|dead)$")


class TestHealthContractSchema:
    """Health endpoint contract tests."""

    def test_health_response_healthy(self) -> None:
        """Verify healthy response matches contract."""
        data = {
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": "2025-12-04T10:00:00Z",
        }
        response = HealthResponseContract.model_validate(data)
        assert response.status == "healthy"

    def test_health_response_unhealthy(self) -> None:
        """Verify unhealthy response matches contract."""
        data = {
            "status": "unhealthy",
            "version": "0.1.0",
            "timestamp": "2025-12-04T10:00:00Z",
        }
        response = HealthResponseContract.model_validate(data)
        assert response.status == "unhealthy"

    def test_health_response_degraded(self) -> None:
        """Verify degraded response matches contract."""
        data = {
            "status": "degraded",
            "version": "0.1.0",
            "timestamp": "2025-12-04T10:00:00Z",
        }
        response = HealthResponseContract.model_validate(data)
        assert response.status == "degraded"

    def test_health_response_invalid_status(self) -> None:
        """Verify invalid status fails contract."""
        data = {
            "status": "unknown",
            "version": "0.1.0",
            "timestamp": "2025-12-04T10:00:00Z",
        }
        with pytest.raises(ValueError):
            HealthResponseContract.model_validate(data)

    def test_readiness_response_ready(self) -> None:
        """Verify ready response matches contract."""
        data = {
            "status": "ready",
            "checks": {"database": True, "redis": True, "kafka": False},
        }
        response = ReadinessResponseContract.model_validate(data)
        assert response.status == "ready"
        assert response.checks is not None
        assert response.checks["database"] is True

    def test_readiness_response_not_ready(self) -> None:
        """Verify not_ready response matches contract."""
        data = {"status": "not_ready", "checks": {"database": False}}
        response = ReadinessResponseContract.model_validate(data)
        assert response.status == "not_ready"

    def test_liveness_response_alive(self) -> None:
        """Verify alive response matches contract."""
        data = {"status": "alive"}
        response = LivenessResponseContract.model_validate(data)
        assert response.status == "alive"

    def test_liveness_response_dead(self) -> None:
        """Verify dead response matches contract."""
        data = {"status": "dead"}
        response = LivenessResponseContract.model_validate(data)
        assert response.status == "dead"
