"""gRPC infrastructure module.

This module provides gRPC server and client infrastructure for
microservice communication, following Clean Architecture principles.
"""

from src.infrastructure.grpc.client.factory import GRPCClientFactory
from src.infrastructure.grpc.health.service import HealthServicer
from src.infrastructure.grpc.server import GRPCServer

__all__ = [
    "GRPCClientFactory",
    "GRPCServer",
    "HealthServicer",
]
