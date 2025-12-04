"""Prometheus metrics infrastructure.

Provides metrics collection, decorators, and FastAPI integration.

**Feature: observability-infrastructure**
**Requirement: R5 - Prometheus Metrics**
"""

from infrastructure.prometheus.config import PrometheusConfig
from infrastructure.prometheus.endpoint import create_metrics_endpoint, setup_prometheus
from infrastructure.prometheus.metrics import (
    count_exceptions,
    counter,
    gauge,
    histogram,
    summary,
    timer,
)
from infrastructure.prometheus.middleware import PrometheusMiddleware
from infrastructure.prometheus.registry import (
    MetricsRegistry,
    get_registry,
)

__all__ = [
    # Config
    "PrometheusConfig",
    # Registry
    "MetricsRegistry",
    "get_registry",
    # Metrics decorators
    "counter",
    "gauge",
    "histogram",
    "summary",
    "timer",
    "count_exceptions",
    # FastAPI
    "PrometheusMiddleware",
    "create_metrics_endpoint",
    "setup_prometheus",
]
