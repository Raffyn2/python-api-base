"""Dapr interface module.

This module provides FastAPI routes for Dapr integration.
"""

from interface.dapr.routes import dapr_router

__all__ = ["dapr_router"]
