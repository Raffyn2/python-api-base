"""Knative configuration models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AutoscalingClass(str, Enum):
    """Knative autoscaling class options."""

    KPA = "kpa.autoscaling.knative.dev"
    HPA = "hpa.autoscaling.knative.dev"


class AutoscalingMetric(str, Enum):
    """Knative autoscaling metric options."""

    CONCURRENCY = "concurrency"
    RPS = "rps"
    CPU = "cpu"
    MEMORY = "memory"


class KnativeManifestError(Exception):
    """Base error for Knative manifest issues."""

    pass


class InvalidTrafficConfigError(KnativeManifestError):
    """Traffic percentages don't sum to 100."""

    pass


class InvalidAutoscalingConfigError(KnativeManifestError):
    """Invalid autoscaling configuration."""

    pass


@dataclass
class TrafficTarget:
    """Traffic target for a Knative revision."""

    revision_name: str
    percent: int
    tag: str | None = None
    latest_revision: bool = False

    def __post_init__(self) -> None:
        """Validate traffic target."""
        if self.percent < 0 or self.percent > 100:
            raise InvalidTrafficConfigError(
                f"Traffic percent must be between 0 and 100, got {self.percent}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to Knative traffic spec format."""
        result: dict[str, Any] = {"percent": self.percent}

        if self.latest_revision:
            result["latestRevision"] = True
        else:
            result["revisionName"] = self.revision_name

        if self.tag:
            result["tag"] = self.tag

        return result


@dataclass
class TrafficConfig:
    """Traffic splitting configuration for Knative Service."""

    targets: list[TrafficTarget]

    def __post_init__(self) -> None:
        """Validate traffic configuration."""
        self.validate()

    def validate(self) -> bool:
        """Validate traffic percentages sum to 100.

        Returns:
            True if valid

        Raises:
            InvalidTrafficConfigError: If percentages don't sum to 100
        """
        total = sum(t.percent for t in self.targets)
        if total != 100:
            raise InvalidTrafficConfigError(
                f"Traffic percentages must sum to 100, got {total}"
            )
        return True

    def to_list(self) -> list[dict[str, Any]]:
        """Convert to Knative traffic spec format."""
        return [t.to_dict() for t in self.targets]


@dataclass
class KnativeServiceConfig:
    """Configuration for Knative Service generation."""

    name: str
    namespace: str
    image: str
    port: int = 8000

    # Autoscaling
    autoscaling_class: AutoscalingClass = AutoscalingClass.KPA
    autoscaling_metric: AutoscalingMetric = AutoscalingMetric.CONCURRENCY
    autoscaling_target: int = 100
    min_scale: int = 0
    max_scale: int = 10
    scale_down_delay: str = "30s"
    scale_to_zero_retention: str = "1m"

    # Resources
    cpu_request: str = "100m"
    cpu_limit: str = "1000m"
    memory_request: str = "256Mi"
    memory_limit: str = "1Gi"

    # Container
    container_concurrency: int = 100
    timeout_seconds: int = 300

    # Health probes
    readiness_path: str = "/health/ready"
    liveness_path: str = "/health/live"

    # Istio
    istio_sidecar: bool = True

    # Labels and annotations
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    # Environment
    env_vars: dict[str, str] = field(default_factory=dict)
    config_map_refs: list[str] = field(default_factory=list)
    secret_refs: list[str] = field(default_factory=list)

    # Traffic
    traffic: TrafficConfig | None = None

    def __post_init__(self) -> None:
        """Validate configuration."""
        self.validate()

    def validate(self) -> None:
        """Validate Knative service configuration.

        Raises:
            InvalidAutoscalingConfigError: If autoscaling config is invalid
        """
        if self.min_scale < 0:
            raise InvalidAutoscalingConfigError("min_scale must be >= 0")
        if self.max_scale < self.min_scale:
            raise InvalidAutoscalingConfigError("max_scale must be >= min_scale")
        if self.autoscaling_target <= 0:
            raise InvalidAutoscalingConfigError("autoscaling_target must be > 0")
        if self.container_concurrency < 0:
            raise InvalidAutoscalingConfigError("container_concurrency must be >= 0")
        if self.timeout_seconds <= 0:
            raise InvalidAutoscalingConfigError("timeout_seconds must be > 0")

    def get_autoscaling_annotations(self) -> dict[str, str]:
        """Get autoscaling annotations for Knative Service.

        Returns:
            Dictionary of autoscaling annotations
        """
        return {
            "autoscaling.knative.dev/class": self.autoscaling_class.value,
            "autoscaling.knative.dev/metric": self.autoscaling_metric.value,
            "autoscaling.knative.dev/target": str(self.autoscaling_target),
            "autoscaling.knative.dev/min-scale": str(self.min_scale),
            "autoscaling.knative.dev/max-scale": str(self.max_scale),
            "autoscaling.knative.dev/scale-down-delay": self.scale_down_delay,
            "autoscaling.knative.dev/scale-to-zero-pod-retention-period": self.scale_to_zero_retention,
        }

    def __eq__(self, other: object) -> bool:
        """Check equality with another KnativeServiceConfig."""
        if not isinstance(other, KnativeServiceConfig):
            return False
        return (
            self.name == other.name
            and self.namespace == other.namespace
            and self.image == other.image
            and self.port == other.port
            and self.autoscaling_class == other.autoscaling_class
            and self.autoscaling_metric == other.autoscaling_metric
            and self.autoscaling_target == other.autoscaling_target
            and self.min_scale == other.min_scale
            and self.max_scale == other.max_scale
            and self.cpu_request == other.cpu_request
            and self.cpu_limit == other.cpu_limit
            and self.memory_request == other.memory_request
            and self.memory_limit == other.memory_limit
            and self.container_concurrency == other.container_concurrency
            and self.timeout_seconds == other.timeout_seconds
        )
