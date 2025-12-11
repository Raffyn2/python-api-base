"""Knative manifest generator."""

from typing import Any

import structlog
import yaml

from infrastructure.eventing.knative.models import KnativeServiceConfig

logger = structlog.get_logger(__name__)


class KnativeManifestGenerator:
    """Generator for Knative Service manifests."""

    @staticmethod
    def generate(config: KnativeServiceConfig) -> dict[str, Any]:
        """Generate Knative Service manifest from configuration.

        Args:
            config: Knative service configuration

        Returns:
            Knative Service manifest as dictionary
        """
        # Build annotations
        annotations = {
            **config.get_autoscaling_annotations(),
            "prometheus.io/scrape": "true",
            "prometheus.io/port": str(config.port),
            "prometheus.io/path": "/metrics",
        }

        if config.istio_sidecar:
            annotations["sidecar.istio.io/inject"] = "true"

        annotations.update(config.annotations)

        # Build labels
        labels = {
            "app.kubernetes.io/name": config.name,
            "app.kubernetes.io/component": "api",
        }
        labels.update(config.labels)

        # Build env vars
        env = [{"name": k, "value": v} for k, v in config.env_vars.items()]

        # Build envFrom
        env_from = [{"configMapRef": {"name": cm}} for cm in config.config_map_refs]
        env_from.extend({"secretRef": {"name": secret, "optional": True}} for secret in config.secret_refs)

        # Build container spec
        container: dict[str, Any] = {
            "name": "api",
            "image": config.image,
            "ports": [
                {
                    "containerPort": config.port,
                    "protocol": "TCP",
                    "name": "http1",
                }
            ],
            "resources": {
                "requests": {
                    "cpu": config.cpu_request,
                    "memory": config.memory_request,
                },
                "limits": {
                    "cpu": config.cpu_limit,
                    "memory": config.memory_limit,
                },
            },
            "readinessProbe": {
                "httpGet": {
                    "path": config.readiness_path,
                    "port": config.port,
                },
                "initialDelaySeconds": 5,
                "periodSeconds": 10,
                "timeoutSeconds": 5,
                "successThreshold": 1,
                "failureThreshold": 3,
            },
            "livenessProbe": {
                "httpGet": {
                    "path": config.liveness_path,
                    "port": config.port,
                },
                "initialDelaySeconds": 10,
                "periodSeconds": 30,
                "timeoutSeconds": 5,
                "successThreshold": 1,
                "failureThreshold": 3,
            },
            "securityContext": {
                "runAsNonRoot": True,
                "readOnlyRootFilesystem": True,
                "allowPrivilegeEscalation": False,
                "capabilities": {"drop": ["ALL"]},
            },
        }

        if env:
            container["env"] = env
        if env_from:
            container["envFrom"] = env_from

        # Build manifest
        manifest: dict[str, Any] = {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {
                "name": config.name,
                "namespace": config.namespace,
                "labels": labels,
            },
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": annotations,
                        "labels": labels,
                    },
                    "spec": {
                        "containerConcurrency": config.container_concurrency,
                        "timeoutSeconds": config.timeout_seconds,
                        "containers": [container],
                    },
                },
            },
        }

        # Add traffic configuration if present
        if config.traffic:
            manifest["spec"]["traffic"] = config.traffic.to_list()

        return manifest

    @staticmethod
    def to_yaml(config: KnativeServiceConfig) -> str:
        """Generate Knative Service manifest as YAML string.

        Args:
            config: Knative service configuration

        Returns:
            YAML string representation
        """
        manifest = KnativeManifestGenerator.generate(config)
        return yaml.dump(manifest, default_flow_style=False, sort_keys=False)

    @staticmethod
    def from_yaml(yaml_str: str) -> KnativeServiceConfig:
        """Parse Knative Service manifest from YAML string.

        Args:
            yaml_str: YAML string representation

        Returns:
            KnativeServiceConfig instance
        """
        manifest = yaml.safe_load(yaml_str)
        return KnativeManifestGenerator.from_dict(manifest)

    @staticmethod
    def from_dict(manifest: dict[str, Any]) -> KnativeServiceConfig:
        """Parse Knative Service manifest from dictionary.

        Args:
            manifest: Manifest dictionary

        Returns:
            KnativeServiceConfig instance
        """
        from infrastructure.eventing.knative.models import (
            AutoscalingClass,
            AutoscalingMetric,
            TrafficConfig,
            TrafficTarget,
        )

        metadata = manifest.get("metadata", {})
        spec = manifest.get("spec", {})
        template = spec.get("template", {})
        template_metadata = template.get("metadata", {})
        template_spec = template.get("spec", {})
        annotations = template_metadata.get("annotations", {})
        containers = template_spec.get("containers", [{}])
        container = containers[0] if containers else {}
        resources = container.get("resources", {})
        requests = resources.get("requests", {})
        limits = resources.get("limits", {})

        # Parse autoscaling class
        autoscaling_class_str = annotations.get("autoscaling.knative.dev/class", "kpa.autoscaling.knative.dev")
        autoscaling_class = AutoscalingClass(autoscaling_class_str)

        # Parse autoscaling metric
        autoscaling_metric_str = annotations.get("autoscaling.knative.dev/metric", "concurrency")
        autoscaling_metric = AutoscalingMetric(autoscaling_metric_str)

        # Parse traffic config
        traffic = None
        if "traffic" in spec:
            targets = [
                TrafficTarget(
                    revision_name=t.get("revisionName", ""),
                    percent=t.get("percent", 0),
                    tag=t.get("tag"),
                    latest_revision=t.get("latestRevision", False),
                )
                for t in spec["traffic"]
            ]
            traffic = TrafficConfig(targets=targets)

        # Get port from container
        ports = container.get("ports", [{}])
        port = ports[0].get("containerPort", 8000) if ports else 8000

        return KnativeServiceConfig(
            name=metadata.get("name", ""),
            namespace=metadata.get("namespace", "default"),
            image=container.get("image", ""),
            port=port,
            autoscaling_class=autoscaling_class,
            autoscaling_metric=autoscaling_metric,
            autoscaling_target=int(annotations.get("autoscaling.knative.dev/target", "100")),
            min_scale=int(annotations.get("autoscaling.knative.dev/min-scale", "0")),
            max_scale=int(annotations.get("autoscaling.knative.dev/max-scale", "10")),
            scale_down_delay=annotations.get("autoscaling.knative.dev/scale-down-delay", "30s"),
            scale_to_zero_retention=annotations.get("autoscaling.knative.dev/scale-to-zero-pod-retention-period", "1m"),
            cpu_request=requests.get("cpu", "100m"),
            cpu_limit=limits.get("cpu", "1000m"),
            memory_request=requests.get("memory", "256Mi"),
            memory_limit=limits.get("memory", "1Gi"),
            container_concurrency=template_spec.get("containerConcurrency", 100),
            timeout_seconds=template_spec.get("timeoutSeconds", 300),
            istio_sidecar=annotations.get("sidecar.istio.io/inject", "true") == "true",
            labels=metadata.get("labels", {}),
            traffic=traffic,
        )
