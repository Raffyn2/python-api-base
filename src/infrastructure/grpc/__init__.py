"""gRPC infrastructure module.

This module provides gRPC server and client infrastructure for
microservice communication, following Clean Architecture principles.
"""

from src.infrastructure.grpc.server import GRPCServer
from src.infrastructure.grpc.client.factory import GRPCClientFactory
from src.infrastructure.grpc.health.service import HealthServicer

__all__ = [
    "GRPCServer",
    "GRPCClientFactory",
    "HealthServicer",
]
