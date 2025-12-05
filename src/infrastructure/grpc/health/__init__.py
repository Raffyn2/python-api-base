"""gRPC health check module.

This module provides health check service implementation
following the gRPC health checking protocol.
"""

from src.infrastructure.grpc.health.service import HealthServicer

__all__ = ["HealthServicer"]
