"""gRPC client module.

This module provides client factory and utilities for creating
resilient gRPC clients with retry and circuit breaker support.
"""

from src.infrastructure.grpc.client.factory import GRPCClientFactory
from src.infrastructure.grpc.client.resilience import CircuitBreakerWrapper

__all__ = ["CircuitBreakerWrapper", "GRPCClientFactory"]
