"""gRPC interface layer module.

This module provides gRPC servicers that integrate with the
application layer following Clean Architecture principles.
"""

from interface.grpc.servicers.base import BaseServicer

__all__ = ["BaseServicer"]
