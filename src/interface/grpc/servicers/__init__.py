"""gRPC servicers module.

This module contains gRPC servicer implementations that handle
RPC requests and delegate to application layer use cases.
"""

from src.interface.grpc.servicers.base import BaseServicer

__all__ = ["BaseServicer"]
