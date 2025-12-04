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
    # Registry
    "MetricsRegistry",
    # Config
    "PrometheusConfig",
    # FastAPI
    "PrometheusMiddleware",
    "count_exceptions",
    # Metrics decorators
    "counter",
    "create_metrics_endpoint",
    "gauge",
    "get_registry",
    "histogram",
    "setup_prometheus",
    "summary",
    "timer",
]
