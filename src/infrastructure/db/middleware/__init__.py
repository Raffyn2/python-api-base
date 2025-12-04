"""Database middleware module.

Provides middleware for database operations monitoring and optimization.
"""

from .query_timing import (
    QueryStats,
    QueryTimingMiddleware,
    install_query_timing,
)
from .query_timing_prometheus import (
    QueryTimingPrometheusMiddleware,
    install_query_timing_with_prometheus,
)

__all__ = [
    "QueryStats",
    "QueryTimingMiddleware",
    "install_query_timing",
    "QueryTimingPrometheusMiddleware",
    "install_query_timing_with_prometheus",
]
