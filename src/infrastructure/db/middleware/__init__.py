"""Database middleware module.

Provides middleware for database operations monitoring and optimization.
"""

from infrastructure.db.middleware.query_timing import (
    QueryStats,
    QueryTimingMiddleware,
    install_query_timing,
)
from infrastructure.db.middleware.query_timing_prometheus import (
    QueryTimingPrometheusMiddleware,
    install_query_timing_with_prometheus,
)

__all__ = [
    "QueryStats",
    "QueryTimingMiddleware",
    "QueryTimingPrometheusMiddleware",
    "install_query_timing",
    "install_query_timing_with_prometheus",
]
