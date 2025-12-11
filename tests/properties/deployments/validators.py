"""
Manifest validation utilities for Kubernetes, Helm, and Terraform configurations.

This module provides validators to ensure deployment manifests follow
security best practices and organizational standards.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Severity(Enum):
    """Validation result severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    rule_id: str
    message: str
    severity: Severity
    file_path: str
    line_number: int | None = None
    suggestion: str | None = None


@dataclass
class ManifestMetadata:
    """Metadata extracted from K8s manifest."""

    api_version: str
    kind: str
    name: str
    namespace: str | None = None
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)


def load_yaml_file(file_path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    with open(file_path) as f:
        return yaml.safe_load(f)


def load_yaml_files(directory: str | Path, pattern: str = "*.yaml") -> list[tuple[Path, dict]]:
    """Load all YAML files from a directory."""
    path = Path(directory)
    results = []
    for file_path in path.rglob(pattern):
        try:
            content = load_yaml_file(file_path)
            if content:
                results.append((file_path, content))
        except (yaml.YAMLError, OSError):
            continue
    return results


class K8sManifestValidator:
    """Validates Kubernetes manifests against security standards."""

    REQUIRED_SECURITY_CONTEXT_FIELDS = [
        "runAsNonRoot",
        "allowPrivilegeEscalation",
        "readOnlyRootFilesystem",
    ]

    REQUIRED_LABELS = [
        "app.kubernetes.io/name",
        "app.kubernetes.io/component",
    ]

    def validate_security_context(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check seccompProfile, runAsNonRoot, capabilities."""
        results = []
        kind = manifest.get("kind", "")

        if kind not in ["Deployment", "StatefulSet", "DaemonSet", "Pod", "Job"]:
            return results

        spec = self._get_pod_spec(manifest)
        if not spec:
            return results

        # Check pod-level security context
        pod_security = spec.get("securityContext", {})
        results.extend(self._validate_pod_security_context(pod_security, file_path))

        # Check container-level security context
        containers = spec.get("containers", [])
        for container in containers:
            container_name = container.get("name", "unknown")
            container_security = container.get("securityContext", {})
            results.extend(self._validate_container_security_context(container_security, container_name, file_path))

        return results

    def _get_pod_spec(self, manifest: dict[str, Any]) -> dict[str, Any] | None:
        """Extract pod spec from various workload types."""
        kind = manifest.get("kind", "")
        if kind == "Pod":
            return manifest.get("spec", {})
        if kind in ["Deployment", "StatefulSet", "DaemonSet", "Job"]:
            return manifest.get("spec", {}).get("template", {}).get("spec", {})
        return None

    def _validate_pod_security_context(
        self, security_context: dict[str, Any], file_path: str
    ) -> list[ValidationResult]:
        """Validate pod-level security context."""
        results = []

        # Check runAsNonRoot
        if not security_context.get("runAsNonRoot", False):
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-SEC-001",
                    message="Pod security context must have runAsNonRoot: true",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    suggestion="Add 'runAsNonRoot: true' to pod securityContext",
                )
            )

        # Check runAsUser
        run_as_user = security_context.get("runAsUser")
        if run_as_user is not None and run_as_user < 1000:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-SEC-002",
                    message=f"runAsUser should be >= 1000, got {run_as_user}",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    suggestion="Set runAsUser to 1000 or higher",
                )
            )

        # Check seccompProfile
        seccomp = security_context.get("seccompProfile", {})
        if seccomp.get("type") != "RuntimeDefault":
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-SEC-003",
                    message="Pod should have seccompProfile.type: RuntimeDefault",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    suggestion="Add 'seccompProfile: type: RuntimeDefault'",
                )
            )

        return results

    def _validate_container_security_context(
        self, security_context: dict[str, Any], container_name: str, file_path: str
    ) -> list[ValidationResult]:
        """Validate container-level security context."""
        results = []

        # Check allowPrivilegeEscalation
        if security_context.get("allowPrivilegeEscalation", True):
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-SEC-004",
                    message=f"Container '{container_name}' must have allowPrivilegeEscalation: false",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    suggestion="Add 'allowPrivilegeEscalation: false'",
                )
            )

        # Check readOnlyRootFilesystem
        if not security_context.get("readOnlyRootFilesystem", False):
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-SEC-005",
                    message=f"Container '{container_name}' should have readOnlyRootFilesystem: true",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Add 'readOnlyRootFilesystem: true'",
                )
            )

        # Check capabilities
        capabilities = security_context.get("capabilities", {})
        drop = capabilities.get("drop", [])
        if "ALL" not in drop:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-SEC-006",
                    message=f"Container '{container_name}' should drop ALL capabilities",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    suggestion="Add 'capabilities: drop: [ALL]'",
                )
            )

        return results

    def validate_network_policy(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check deny-all default and explicit allow rules."""
        results = []

        if manifest.get("kind") != "NetworkPolicy":
            return results

        spec = manifest.get("spec", {})
        policy_types = spec.get("policyTypes", [])

        # Check both Ingress and Egress are defined
        if "Ingress" not in policy_types:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-NET-001",
                    message="NetworkPolicy should include Ingress in policyTypes",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Add 'Ingress' to policyTypes",
                )
            )

        if "Egress" not in policy_types:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="K8S-NET-002",
                    message="NetworkPolicy should include Egress in policyTypes",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Add 'Egress' to policyTypes",
                )
            )

        return results

    def validate_resources(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check requests and limits are defined."""
        results = []
        kind = manifest.get("kind", "")

        if kind not in ["Deployment", "StatefulSet", "DaemonSet", "Pod", "Job"]:
            return results

        spec = self._get_pod_spec(manifest)
        if not spec:
            return results

        containers = spec.get("containers", [])
        for container in containers:
            container_name = container.get("name", "unknown")
            resources = container.get("resources", {})

            requests = resources.get("requests", {})
            limits = resources.get("limits", {})

            if "cpu" not in requests or "memory" not in requests:
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="K8S-RES-001",
                        message=f"Container '{container_name}' missing resource requests",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion="Add 'resources.requests.cpu' and 'resources.requests.memory'",
                    )
                )

            if "cpu" not in limits or "memory" not in limits:
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="K8S-RES-002",
                        message=f"Container '{container_name}' missing resource limits",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion="Add 'resources.limits.cpu' and 'resources.limits.memory'",
                    )
                )

        return results

    def validate_labels(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check kubernetes.io label convention."""
        results = []
        metadata = manifest.get("metadata", {})
        labels = metadata.get("labels", {})

        for required_label in self.REQUIRED_LABELS:
            if required_label not in labels:
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="K8S-LBL-001",
                        message=f"Missing required label: {required_label}",
                        severity=Severity.WARNING,
                        file_path=file_path,
                        suggestion=f"Add label '{required_label}'",
                    )
                )

        return results

    def validate_probes(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check liveness and readiness probes are configured."""
        results = []
        kind = manifest.get("kind", "")

        if kind not in ["Deployment", "StatefulSet", "DaemonSet"]:
            return results

        spec = self._get_pod_spec(manifest)
        if not spec:
            return results

        containers = spec.get("containers", [])
        for container in containers:
            container_name = container.get("name", "unknown")

            if "livenessProbe" not in container:
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="K8S-PRB-001",
                        message=f"Container '{container_name}' missing livenessProbe",
                        severity=Severity.WARNING,
                        file_path=file_path,
                        suggestion="Add livenessProbe configuration",
                    )
                )

            if "readinessProbe" not in container:
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="K8S-PRB-002",
                        message=f"Container '{container_name}' missing readinessProbe",
                        severity=Severity.WARNING,
                        file_path=file_path,
                        suggestion="Add readinessProbe configuration",
                    )
                )

        return results


class HelmChartValidator:
    """Validates Helm charts against best practices."""

    def validate_values(
        self, values: dict[str, Any], env: str = "production", file_path: str = ""
    ) -> list[ValidationResult]:
        """Check required values and no 'latest' tags."""
        results = []

        # Check image tag
        image = values.get("image", {})
        tag = image.get("tag", "")
        if tag == "" or tag == "latest":
            if env == "production":
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="HELM-IMG-001",
                        message="Image tag cannot be empty or 'latest' in production",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion="Set a specific version tag",
                    )
                )

        # Check external secrets in production
        external_secrets = values.get("externalSecrets", {})
        if env == "production" and not external_secrets.get("enabled", False):
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="HELM-SEC-001",
                    message="externalSecrets must be enabled in production",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    suggestion="Set 'externalSecrets.enabled: true'",
                )
            )

        # Check resources are defined
        resources = values.get("resources", {})
        if not resources.get("requests") or not resources.get("limits"):
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="HELM-RES-001",
                    message="Resources requests and limits must be defined",
                    severity=Severity.ERROR,
                    file_path=file_path,
                    suggestion="Define 'resources.requests' and 'resources.limits'",
                )
            )

        return results

    def validate_chart(self, chart: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Validate Chart.yaml contents."""
        results = []

        # Check required fields
        required_fields = ["apiVersion", "name", "version", "appVersion"]
        for field_name in required_fields:
            if field_name not in chart:
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="HELM-CHT-001",
                        message=f"Chart.yaml missing required field: {field_name}",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion=f"Add '{field_name}' to Chart.yaml",
                    )
                )

        return results


class TerraformValidator:
    """Validates Terraform configurations."""

    def validate_backend(self, config: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check encrypted backend with state locking."""
        results = []

        terraform = config.get("terraform", {})
        backend = terraform.get("backend", {})

        # Check S3 backend encryption
        s3_backend = backend.get("s3", {})
        if s3_backend:
            if not s3_backend.get("encrypt", False):
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="TF-BCK-001",
                        message="S3 backend must have encrypt = true",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion="Add 'encrypt = true' to backend configuration",
                    )
                )

            if not s3_backend.get("dynamodb_table"):
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="TF-BCK-002",
                        message="S3 backend should have DynamoDB table for state locking",
                        severity=Severity.WARNING,
                        file_path=file_path,
                        suggestion="Add 'dynamodb_table' for state locking",
                    )
                )

        return results

    def validate_variables(self, variables: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check sensitive marking and validations."""
        results = []

        sensitive_keywords = ["password", "secret", "key", "token", "credential"]

        for var_name, var_config in variables.items():
            # Check if sensitive variables are marked
            var_name_lower = var_name.lower()
            is_sensitive_name = any(kw in var_name_lower for kw in sensitive_keywords)

            if is_sensitive_name and not var_config.get("sensitive", False):
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="TF-VAR-001",
                        message=f"Variable '{var_name}' should be marked as sensitive",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion="Add 'sensitive = true' to variable definition",
                    )
                )

        return results

    def validate_provider_versions(self, config: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check provider version constraints."""
        results = []

        terraform = config.get("terraform", {})
        required_providers = terraform.get("required_providers", {})

        for provider_name, provider_config in required_providers.items():
            version = provider_config.get("version", "")
            if not version:
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="TF-PRV-001",
                        message=f"Provider '{provider_name}' missing version constraint",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion="Add version constraint like '~> 5.0'",
                    )
                )

        return results


class DockerComposeValidator:
    """Validates Docker Compose configurations."""

    def validate_service(
        self, service: dict[str, Any], service_name: str, file_path: str = ""
    ) -> list[ValidationResult]:
        """Validate a Docker Compose service."""
        results = []

        # Check read_only
        if not service.get("read_only", False):
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="DCK-SEC-001",
                    message=f"Service '{service_name}' should have read_only: true",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Add 'read_only: true' for security",
                )
            )

        # Check security_opt
        security_opt = service.get("security_opt", [])
        if "no-new-privileges:true" not in security_opt:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="DCK-SEC-002",
                    message=f"Service '{service_name}' should have no-new-privileges",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Add 'security_opt: [no-new-privileges:true]'",
                )
            )

        # Check healthcheck
        if "healthcheck" not in service:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="DCK-HLT-001",
                    message=f"Service '{service_name}' missing healthcheck",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Add healthcheck configuration",
                )
            )

        # Check resource limits
        deploy = service.get("deploy", {})
        resources = deploy.get("resources", {})
        if not resources.get("limits"):
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="DCK-RES-001",
                    message=f"Service '{service_name}' missing resource limits",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Add 'deploy.resources.limits'",
                )
            )

        return results


class IstioValidator:
    """Validates Istio configurations."""

    def validate_peer_authentication(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check mTLS configuration."""
        results = []

        if manifest.get("kind") != "PeerAuthentication":
            return results

        spec = manifest.get("spec", {})
        mtls = spec.get("mtls", {})
        mode = mtls.get("mode", "")

        if mode != "STRICT":
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="IST-SEC-001",
                    message="PeerAuthentication should have mtls.mode: STRICT",
                    severity=Severity.WARNING,
                    file_path=file_path,
                    suggestion="Set 'mtls.mode: STRICT' for production",
                )
            )

        return results

    def validate_authorization_policy(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check authorization policy configuration."""
        results = []

        if manifest.get("kind") != "AuthorizationPolicy":
            return results

        # Check if it's a deny-all policy
        spec = manifest.get("spec", {})
        if not spec:
            # Empty spec means deny-all, which is good
            return results

        return results

    def validate_envoy_filter(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Check EnvoyFilter for rate limiting."""
        results = []

        if manifest.get("kind") != "EnvoyFilter":
            return results

        spec = manifest.get("spec", {})
        config_patches = spec.get("configPatches", [])

        has_rate_limit = False
        for patch in config_patches:
            value = patch.get("patch", {}).get("value", {})
            if "local_ratelimit" in str(value):
                has_rate_limit = True
                break

        if not has_rate_limit:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="IST-RL-001",
                    message="EnvoyFilter should configure rate limiting",
                    severity=Severity.INFO,
                    file_path=file_path,
                    suggestion="Add local_ratelimit configuration",
                )
            )

        return results


class KnativeValidator:
    """Validates Knative configurations."""

    def validate_service(self, manifest: dict[str, Any], file_path: str = "") -> list[ValidationResult]:
        """Validate Knative Service configuration."""
        results = []

        if manifest.get("kind") != "Service" or "serving.knative.dev" not in manifest.get("apiVersion", ""):
            return results

        spec = manifest.get("spec", {})
        template = spec.get("template", {})
        annotations = template.get("metadata", {}).get("annotations", {})

        # Check autoscaling annotations
        if "autoscaling.knative.dev/min-scale" not in annotations:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="KN-AS-001",
                    message="Knative Service should have min-scale annotation",
                    severity=Severity.INFO,
                    file_path=file_path,
                    suggestion="Add 'autoscaling.knative.dev/min-scale' annotation",
                )
            )

        if "autoscaling.knative.dev/max-scale" not in annotations:
            results.append(
                ValidationResult(
                    passed=False,
                    rule_id="KN-AS-002",
                    message="Knative Service should have max-scale annotation",
                    severity=Severity.INFO,
                    file_path=file_path,
                    suggestion="Add 'autoscaling.knative.dev/max-scale' annotation",
                )
            )

        # Check security context in container
        container_spec = template.get("spec", {})
        containers = container_spec.get("containers", [])
        for container in containers:
            security_context = container.get("securityContext", {})
            if not security_context.get("runAsNonRoot", False):
                results.append(
                    ValidationResult(
                        passed=False,
                        rule_id="KN-SEC-001",
                        message="Knative container should have runAsNonRoot: true",
                        severity=Severity.ERROR,
                        file_path=file_path,
                        suggestion="Add 'runAsNonRoot: true' to securityContext",
                    )
                )

        return results
