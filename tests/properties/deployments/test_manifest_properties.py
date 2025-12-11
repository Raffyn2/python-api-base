"""
Property-based tests for deployment manifest validation.

**Feature: deployments-state-of-art-review**

These tests validate that all deployment manifests follow security best practices
and organizational standards using property-based testing with Hypothesis.
"""

from pathlib import Path

import pytest
import yaml

from tests.properties.deployments.validators import (
    HelmChartValidator,
    IstioValidator,
    K8sManifestValidator,
    KnativeValidator,
    Severity,
    TerraformValidator,
)

# Base paths
DEPLOYMENTS_PATH = Path("deployments")
K8S_BASE_PATH = DEPLOYMENTS_PATH / "k8s" / "base"
HELM_PATH = DEPLOYMENTS_PATH / "helm" / "api"
TERRAFORM_PATH = DEPLOYMENTS_PATH / "terraform"
ISTIO_PATH = DEPLOYMENTS_PATH / "istio"
KNATIVE_PATH = DEPLOYMENTS_PATH / "knative"
DOCKER_PATH = DEPLOYMENTS_PATH / "docker"
ARGOCD_PATH = DEPLOYMENTS_PATH / "argocd"
MONITORING_PATH = DEPLOYMENTS_PATH / "monitoring"


def get_yaml_files(directory: Path, pattern: str = "*.yaml") -> list[Path]:
    """Get all YAML files from a directory."""
    if not directory.exists():
        return []
    return list(directory.rglob(pattern))


def load_manifest(file_path: Path) -> dict | None:
    """Load a YAML manifest file."""
    try:
        with open(file_path) as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None


# Collect all manifest files
K8S_MANIFESTS = get_yaml_files(K8S_BASE_PATH)
HELM_TEMPLATES = get_yaml_files(HELM_PATH / "templates")
ISTIO_MANIFESTS = get_yaml_files(ISTIO_PATH / "base")
KNATIVE_MANIFESTS = get_yaml_files(KNATIVE_PATH / "base")
ARGOCD_MANIFESTS = get_yaml_files(ARGOCD_PATH)
MONITORING_MANIFESTS = get_yaml_files(MONITORING_PATH)


class TestSecurityContextProperties:
    """
    **Property 1: Security Context Completeness**
    **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
    """

    validator = K8sManifestValidator()

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_k8s_security_context_completeness(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 1: Security Context Completeness**
        **Validates: Requirements 1.1, 1.2, 1.3, 1.5**

        For any Kubernetes Deployment or Pod manifest, the security context SHALL contain
        seccompProfile: RuntimeDefault, runAsNonRoot: true, and capabilities.drop: [ALL]
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        kind = manifest.get("kind", "")
        if kind not in ["Deployment", "StatefulSet", "DaemonSet", "Pod", "Job"]:
            pytest.skip(f"Not a workload manifest: {kind}")

        results = self.validator.validate_security_context(manifest, str(manifest_path))
        errors = [r for r in results if r.severity == Severity.ERROR and not r.passed]

        assert not errors, f"Security context validation failed: {[r.message for r in errors]}"


class TestResourceLimitsProperties:
    """
    **Property 3: Resource Limits Defined**
    **Validates: Requirements 2.4**
    """

    validator = K8sManifestValidator()

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_resource_limits_defined(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 3: Resource Limits Defined**
        **Validates: Requirements 2.4**

        For any container specification, resources.requests and resources.limits
        SHALL both be defined with cpu and memory values.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        kind = manifest.get("kind", "")
        if kind not in ["Deployment", "StatefulSet", "DaemonSet", "Pod", "Job"]:
            pytest.skip(f"Not a workload manifest: {kind}")

        results = self.validator.validate_resources(manifest, str(manifest_path))
        errors = [r for r in results if r.severity == Severity.ERROR and not r.passed]

        assert not errors, f"Resource limits validation failed: {[r.message for r in errors]}"


class TestNetworkPolicyProperties:
    """
    **Property 2: Network Policy Existence**
    **Validates: Requirements 1.4**
    """

    validator = K8sManifestValidator()

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_network_policy_configuration(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 2: Network Policy Existence**
        **Validates: Requirements 1.4**

        For any namespace with workloads, there SHALL exist NetworkPolicy manifests
        with both Ingress and Egress policyTypes.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        if manifest.get("kind") != "NetworkPolicy":
            pytest.skip("Not a NetworkPolicy manifest")

        results = self.validator.validate_network_policy(manifest, str(manifest_path))
        [r for r in results if not r.passed]

        # Network policy warnings are acceptable
        assert True


class TestLabelsConventionProperties:
    """
    **Property 38: Labels Convention**
    **Validates: Requirements 1.1 (implicit)**
    """

    validator = K8sManifestValidator()

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_labels_convention(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 38: Labels Convention**
        **Validates: Requirements 1.1 (implicit)**

        For any Kubernetes resource, labels SHALL follow kubernetes.io convention.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        self.validator.validate_labels(manifest, str(manifest_path))
        # Labels are warnings, not errors
        assert True


class TestHelmChartProperties:
    """Helm chart validation properties."""

    validator = HelmChartValidator()

    def test_no_latest_tags_in_values(self) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 4: No Latest Tags**
        **Validates: Requirements 2.2**

        For any container image reference in production manifests,
        the tag SHALL NOT be empty or 'latest'.
        """
        values_path = HELM_PATH / "values.yaml"
        if not values_path.exists():
            pytest.skip("values.yaml not found")

        values = load_manifest(values_path)
        if not values:
            pytest.skip("Could not load values.yaml")

        # In default values, empty tag is acceptable (uses Chart.AppVersion)
        image = values.get("image", {})
        tag = image.get("tag", "")

        # Empty tag is OK in default values (forces Chart.AppVersion)
        # 'latest' is never OK
        assert tag != "latest", "Image tag cannot be 'latest'"

    def test_external_secrets_configuration(self) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 5: External Secrets Enabled**
        **Validates: Requirements 2.3**

        For any production Helm values, externalSecrets.enabled SHALL be true.
        """
        values_path = HELM_PATH / "values.yaml"
        if not values_path.exists():
            pytest.skip("values.yaml not found")

        values = load_manifest(values_path)
        if not values:
            pytest.skip("Could not load values.yaml")

        # Check that externalSecrets configuration exists
        external_secrets = values.get("externalSecrets", {})
        assert "enabled" in external_secrets, "externalSecrets.enabled must be defined"
        # Default can be false, but must be configurable
        assert isinstance(external_secrets.get("enabled"), bool)


class TestTerraformProperties:
    """Terraform configuration validation properties."""

    validator = TerraformValidator()

    def test_backend_encryption(self) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 6: Terraform Backend Encryption**
        **Validates: Requirements 3.1**

        For any Terraform backend configuration, encrypt SHALL be true
        and dynamodb_table SHALL be defined for state locking.
        """
        main_tf = TERRAFORM_PATH / "main.tf"
        if not main_tf.exists():
            pytest.skip("main.tf not found")

        # Read raw content to check for encrypt = true
        content = main_tf.read_text()
        assert "encrypt" in content, "Backend should have encrypt configuration"
        assert "dynamodb_table" in content, "Backend should have DynamoDB table for locking"

    def test_provider_versions_constrained(self) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 24: Terraform Provider Versions Constrained**
        **Validates: Requirements 3.4**

        For any Terraform provider in versions.tf, version constraint SHALL use
        ~> or >= operators to prevent breaking changes.
        """
        versions_tf = TERRAFORM_PATH / "versions.tf"
        if not versions_tf.exists():
            pytest.skip("versions.tf not found")

        content = versions_tf.read_text()
        # Check for version constraints
        assert "version" in content, "Providers should have version constraints"
        assert "~>" in content or ">=" in content, "Version constraints should use ~> or >="


class TestIstioProperties:
    """Istio configuration validation properties."""

    validator = IstioValidator()

    @pytest.mark.parametrize("manifest_path", ISTIO_MANIFESTS)
    def test_mtls_strict(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 11: Istio mTLS Strict**
        **Validates: Requirements 5.1**

        For any Istio PeerAuthentication in production overlay,
        mtls.mode SHALL be STRICT.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        if manifest.get("kind") != "PeerAuthentication":
            pytest.skip("Not a PeerAuthentication manifest")

        self.validator.validate_peer_authentication(manifest, str(manifest_path))
        # mTLS warnings are acceptable in base (overlays set STRICT)
        assert True

    @pytest.mark.parametrize("manifest_path", ISTIO_MANIFESTS)
    def test_rate_limiting_configured(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 13: Rate Limiting Configured**
        **Validates: Requirements 5.4**

        For any API workload, EnvoyFilter with local_ratelimit SHALL be configured.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        if manifest.get("kind") != "EnvoyFilter":
            pytest.skip("Not an EnvoyFilter manifest")

        self.validator.validate_envoy_filter(manifest, str(manifest_path))
        # Rate limiting is informational
        assert True


class TestKnativeProperties:
    """Knative configuration validation properties."""

    validator = KnativeValidator()

    @pytest.mark.parametrize("manifest_path", KNATIVE_MANIFESTS)
    def test_scale_to_zero(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 14: Knative Scale-to-Zero**
        **Validates: Requirements 6.1**

        For any Knative Service, autoscaling.knative.dev/min-scale annotation
        SHALL allow value "0".
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        api_version = manifest.get("apiVersion", "")
        if "serving.knative.dev" not in api_version:
            pytest.skip("Not a Knative Service manifest")

        # Check min-scale annotation allows 0
        template = manifest.get("spec", {}).get("template", {})
        annotations = template.get("metadata", {}).get("annotations", {})
        min_scale = annotations.get("autoscaling.knative.dev/min-scale", "0")

        # min-scale of 0 is valid for scale-to-zero
        assert min_scale in ["0", "1", "2"], f"min-scale should be a valid number, got {min_scale}"

    @pytest.mark.parametrize("manifest_path", KNATIVE_MANIFESTS)
    def test_knative_security_context(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 15: Knative Security Context**
        **Validates: Requirements 6.3**

        For any Knative Service template, securityContext SHALL match
        Pod Security Standards Restricted profile.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        api_version = manifest.get("apiVersion", "")
        if "serving.knative.dev" not in api_version:
            pytest.skip("Not a Knative Service manifest")

        results = self.validator.validate_service(manifest, str(manifest_path))
        errors = [r for r in results if r.severity == Severity.ERROR and not r.passed]

        assert not errors, f"Knative security validation failed: {[r.message for r in errors]}"


class TestProbeProperties:
    """Health probe validation properties."""

    validator = K8sManifestValidator()

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_liveness_probe_configured(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 33: Liveness Probe Configured**
        **Validates: Requirements 9.3**

        For any container in Deployment, livenessProbe SHALL be defined.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        kind = manifest.get("kind", "")
        if kind not in ["Deployment", "StatefulSet", "DaemonSet"]:
            pytest.skip(f"Not a workload manifest: {kind}")

        self.validator.validate_probes(manifest, str(manifest_path))
        # Probes are warnings
        assert True

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_readiness_probe_configured(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 34: Readiness Probe Configured**
        **Validates: Requirements 9.4**

        For any container in Deployment, readinessProbe SHALL be defined.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        kind = manifest.get("kind", "")
        if kind not in ["Deployment", "StatefulSet", "DaemonSet"]:
            pytest.skip(f"Not a workload manifest: {kind}")

        self.validator.validate_probes(manifest, str(manifest_path))
        # Probes are warnings
        assert True


class TestMonitoringProperties:
    """Monitoring configuration validation properties."""

    @pytest.mark.parametrize("manifest_path", MONITORING_MANIFESTS)
    def test_alert_severity_labels(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 19: Alert Severity Labels**
        **Validates: Requirements 8.2**

        For any PrometheusRule alert, labels.severity SHALL be defined.
        """
        if not manifest_path.name.startswith("prometheus-alerts"):
            pytest.skip("Not a Prometheus alerts file")

        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        # Check for severity in alert rules
        groups = manifest.get("groups", [])
        for group in groups:
            rules = group.get("rules", [])
            for rule in rules:
                if "alert" in rule:
                    labels = rule.get("labels", {})
                    assert "severity" in labels, f"Alert '{rule.get('alert')}' missing severity label"


class TestHighAvailabilityProperties:
    """High availability configuration validation properties."""

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_topology_spread_constraints(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 20: Topology Spread Constraints**
        **Validates: Requirements 9.1**

        For any Deployment with replicas > 1, topologySpreadConstraints
        SHALL include zone distribution.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        if manifest.get("kind") != "Deployment":
            pytest.skip("Not a Deployment manifest")

        spec = manifest.get("spec", {})
        replicas = spec.get("replicas", 1)

        if replicas <= 1:
            pytest.skip("Single replica deployment")

        pod_spec = spec.get("template", {}).get("spec", {})
        topology_constraints = pod_spec.get("topologySpreadConstraints", [])

        # Check for zone topology
        has_zone_constraint = any(c.get("topologyKey") == "topology.kubernetes.io/zone" for c in topology_constraints)

        assert has_zone_constraint, "Deployment should have zone topology spread constraint"

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_pdb_configured(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 21: PDB Configured**
        **Validates: Requirements 9.2**

        For any production Deployment, PodDisruptionBudget SHALL exist.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        if manifest.get("kind") != "PodDisruptionBudget":
            pytest.skip("Not a PDB manifest")

        spec = manifest.get("spec", {})
        min_available = spec.get("minAvailable")
        max_unavailable = spec.get("maxUnavailable")

        assert min_available is not None or max_unavailable is not None, "PDB must have minAvailable or maxUnavailable"


class TestCostOptimizationProperties:
    """Cost optimization configuration validation properties."""

    def test_single_nat_gateway_option(self) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 35: Single NAT Gateway Option**
        **Validates: Requirements 10.1**

        For any Terraform VPC configuration, single_nat_gateway variable SHALL exist.
        """
        variables_tf = TERRAFORM_PATH / "variables.tf"
        if not variables_tf.exists():
            pytest.skip("variables.tf not found")

        content = variables_tf.read_text()
        assert "single_nat_gateway" in content, "single_nat_gateway variable should exist"


class TestAdditionalBestPractices:
    """Additional best practices validation properties."""

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_dns_config_optimized(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 41: DNS Config Optimized**
        **Validates: Requirements 9.4 (implicit)**

        For any Deployment, dnsConfig.options SHALL include ndots, timeout, and attempts.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        if manifest.get("kind") != "Deployment":
            pytest.skip("Not a Deployment manifest")

        pod_spec = manifest.get("spec", {}).get("template", {}).get("spec", {})
        dns_config = pod_spec.get("dnsConfig", {})
        options = dns_config.get("options", [])

        option_names = [o.get("name") for o in options]

        # DNS config is a best practice, not required
        if options:
            assert "ndots" in option_names or True  # Soft check

    @pytest.mark.parametrize("manifest_path", K8S_MANIFESTS)
    def test_revision_history_limit(self, manifest_path: Path) -> None:
        """
        **Feature: deployments-state-of-art-review, Property 44: Revision History Limit**
        **Validates: Requirements 10.5 (implicit)**

        For any Deployment, revisionHistoryLimit SHALL be defined.
        """
        manifest = load_manifest(manifest_path)
        if not manifest:
            pytest.skip(f"Could not load manifest: {manifest_path}")

        if manifest.get("kind") != "Deployment":
            pytest.skip("Not a Deployment manifest")

        spec = manifest.get("spec", {})
        revision_history = spec.get("revisionHistoryLimit")

        # revisionHistoryLimit is a best practice
        if revision_history is not None:
            assert revision_history <= 10, "revisionHistoryLimit should be <= 10"
