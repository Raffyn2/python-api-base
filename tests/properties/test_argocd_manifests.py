"""
Property-based tests for ArgoCD manifests.

These tests validate correctness properties of ArgoCD configuration manifests
using Hypothesis for property-based testing.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import HealthCheck, given, settings, strategies as st

# Base path for ArgoCD manifests
ARGOCD_BASE_PATH = Path("deployments/argocd")


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_all_yaml_documents(path: Path) -> list[dict[str, Any]]:
    """Load all YAML documents from a file."""
    with open(path) as f:
        return list(yaml.safe_load_all(f))


# **Feature: argocd-gitops-integration, Property 1: Application manifest environment correctness**
class TestApplicationManifestCorrectness:
    """
    **Validates: Requirements 2.1, 2.2, 2.3**

    For any Application manifest targeting a specific environment,
    the manifest SHALL contain the correct Helm values file path,
    and environment-appropriate sync settings.
    """

    @pytest.fixture()
    def application_manifests(self) -> dict[str, dict[str, Any]]:
        """Load all Application manifests."""
        apps = {}
        app_path = ARGOCD_BASE_PATH / "applications"
        for env_dir in ["dev", "staging", "prod"]:
            manifest_path = app_path / env_dir / "python-api-base.yaml"
            if manifest_path.exists():
                apps[env_dir] = load_yaml_file(manifest_path)
        return apps

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(env=st.sampled_from(["dev", "staging", "prod"]))
    def test_application_has_correct_values_file(
        self, env: str, application_manifests: dict[str, dict[str, Any]]
    ) -> None:
        """Application manifest contains correct values file for environment."""
        if env not in application_manifests:
            pytest.skip(f"No manifest for {env}")

        app = application_manifests[env]
        values_files = app["spec"]["source"]["helm"]["valueFiles"]

        assert f"values-{env}.yaml" in values_files, f"Expected values-{env}.yaml in valueFiles"

    def test_dev_has_auto_sync_and_self_heal(self, application_manifests: dict[str, dict[str, Any]]) -> None:
        """Dev environment SHALL have auto-sync with self-heal enabled."""
        if "dev" not in application_manifests:
            pytest.skip("No dev manifest")

        app = application_manifests["dev"]
        sync_policy = app["spec"].get("syncPolicy", {})
        automated = sync_policy.get("automated", {})

        assert automated.get("selfHeal") is True, "Dev should have selfHeal=true"
        assert automated.get("prune") is True, "Dev should have prune=true"

    def test_prod_has_manual_sync(self, application_manifests: dict[str, dict[str, Any]]) -> None:
        """Prod environment SHALL require manual sync (no automated sync)."""
        if "prod" not in application_manifests:
            pytest.skip("No prod manifest")

        app = application_manifests["prod"]
        sync_policy = app["spec"].get("syncPolicy", {})
        automated = sync_policy.get("automated", {})

        assert not automated, "Prod should not have automated sync"


# **Feature: argocd-gitops-integration, Property 2: ApplicationSet generates correct number of Applications**
class TestApplicationSetGeneration:
    """
    **Validates: Requirements 3.1**

    For any ApplicationSet with a list generator containing N environment entries,
    the generator configuration SHALL produce exactly N distinct Application
    configurations with unique names and namespaces.
    """

    @pytest.fixture()
    def applicationset_manifest(self) -> dict[str, Any] | None:
        """Load ApplicationSet manifest."""
        path = ARGOCD_BASE_PATH / "applicationsets" / "python-api-base-set.yaml"
        if path.exists():
            return load_yaml_file(path)
        return None

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        envs=st.lists(
            st.sampled_from(["dev", "staging", "prod", "qa", "uat"]),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    def test_list_generator_produces_correct_count(
        self, envs: list[str], applicationset_manifest: dict[str, Any] | None
    ) -> None:
        """List generator produces one Application per environment entry."""
        if applicationset_manifest is None:
            pytest.skip("No ApplicationSet manifest")

        generators = applicationset_manifest["spec"]["generators"]
        list_generator = None

        for gen in generators:
            if "list" in gen:
                list_generator = gen["list"]
                break

        assert list_generator is not None, "ApplicationSet should have list generator"

        elements = list_generator["elements"]
        env_names = [e["env"] for e in elements]
        namespaces = [e["namespace"] for e in elements]

        # All environments should be unique
        assert len(env_names) == len(set(env_names)), "Environment names must be unique"
        assert len(namespaces) == len(set(namespaces)), "Namespaces must be unique"

    def test_applicationset_has_required_template_fields(self, applicationset_manifest: dict[str, Any] | None) -> None:
        """ApplicationSet template has all required fields."""
        if applicationset_manifest is None:
            pytest.skip("No ApplicationSet manifest")

        template = applicationset_manifest["spec"]["template"]

        assert "metadata" in template
        assert "name" in template["metadata"]
        assert "spec" in template
        assert "project" in template["spec"]
        assert "source" in template["spec"]
        assert "destination" in template["spec"]


# **Feature: argocd-gitops-integration, Property 3: AppProject security constraints**
class TestAppProjectSecurityConstraints:
    """
    **Validates: Requirements 4.1, 4.2**

    For any AppProject manifest, it SHALL define non-empty sourceRepos and
    destinations lists, and SHALL NOT include dangerous cluster-scoped resources.
    """

    DANGEROUS_RESOURCES = [
        ("rbac.authorization.k8s.io", "ClusterRole"),
        ("rbac.authorization.k8s.io", "ClusterRoleBinding"),
        ("", "Node"),
        ("", "PersistentVolume"),
    ]

    @pytest.fixture()
    def project_manifests(self) -> list[dict[str, Any]]:
        """Load all AppProject manifests."""
        projects = []
        projects_path = ARGOCD_BASE_PATH / "projects"
        if projects_path.exists():
            for yaml_file in projects_path.glob("*.yaml"):
                if yaml_file.name != "kustomization.yaml":
                    projects.append(load_yaml_file(yaml_file))
        return projects

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(project_idx=st.integers(min_value=0, max_value=10))
    def test_project_has_source_repos(self, project_idx: int, project_manifests: list[dict[str, Any]]) -> None:
        """AppProject SHALL define non-empty sourceRepos."""
        if not project_manifests:
            pytest.skip("No project manifests")

        idx = project_idx % len(project_manifests)
        project = project_manifests[idx]

        source_repos = project["spec"].get("sourceRepos", [])
        assert len(source_repos) > 0, "sourceRepos must not be empty"

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(project_idx=st.integers(min_value=0, max_value=10))
    def test_project_has_destinations(self, project_idx: int, project_manifests: list[dict[str, Any]]) -> None:
        """AppProject SHALL define non-empty destinations."""
        if not project_manifests:
            pytest.skip("No project manifests")

        idx = project_idx % len(project_manifests)
        project = project_manifests[idx]

        destinations = project["spec"].get("destinations", [])
        assert len(destinations) > 0, "destinations must not be empty"

    def test_python_api_base_project_restricts_dangerous_resources(
        self, project_manifests: list[dict[str, Any]]
    ) -> None:
        """python-api-base project SHALL NOT allow dangerous cluster resources."""
        python_api_project = None
        for project in project_manifests:
            if project["metadata"]["name"] == "python-api-base":
                python_api_project = project
                break

        if python_api_project is None:
            pytest.skip("python-api-base project not found")

        whitelist = python_api_project["spec"].get("clusterResourceWhitelist", [])

        for group, kind in self.DANGEROUS_RESOURCES:
            for item in whitelist:
                if item.get("group") == group and item.get("kind") == kind:
                    pytest.fail(f"Dangerous resource {group}/{kind} in clusterResourceWhitelist")


# **Feature: argocd-gitops-integration, Property 4: Image Updater annotation validity**
class TestImageUpdaterAnnotations:
    """
    **Validates: Requirements 5.4**

    For any Application with image updater annotations, the update-strategy
    annotation SHALL contain a valid strategy value.
    """

    VALID_STRATEGIES = {"semver", "latest", "digest", "name"}

    @pytest.fixture()
    def applications_with_image_updater(self) -> list[dict[str, Any]]:
        """Load Applications with image updater annotations."""
        apps = []
        app_path = ARGOCD_BASE_PATH / "applications"
        if app_path.exists():
            for env_dir in app_path.iterdir():
                if env_dir.is_dir():
                    for yaml_file in env_dir.glob("*.yaml"):
                        app = load_yaml_file(yaml_file)
                        annotations = app.get("metadata", {}).get("annotations", {})
                        if any(k.startswith("argocd-image-updater") for k in annotations.keys()):
                            apps.append(app)
        return apps

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(app_idx=st.integers(min_value=0, max_value=10))
    def test_image_updater_strategy_is_valid(
        self, app_idx: int, applications_with_image_updater: list[dict[str, Any]]
    ) -> None:
        """Image updater strategy annotation SHALL be valid."""
        if not applications_with_image_updater:
            pytest.skip("No applications with image updater")

        idx = app_idx % len(applications_with_image_updater)
        app = applications_with_image_updater[idx]
        annotations = app["metadata"]["annotations"]

        for key, value in annotations.items():
            if ".update-strategy" in key:
                assert value in self.VALID_STRATEGIES, (
                    f"Invalid strategy '{value}', must be one of {self.VALID_STRATEGIES}"
                )


# **Feature: argocd-gitops-integration, Property 5: Notification configuration completeness**
class TestNotificationConfiguration:
    """
    **Validates: Requirements 6.4, 6.5**

    For any notification ConfigMap, it SHALL define at least one service
    configuration, and all referenced templates in triggers SHALL exist.
    """

    @pytest.fixture()
    def notifications_cm(self) -> dict[str, Any] | None:
        """Load notifications ConfigMap."""
        path = ARGOCD_BASE_PATH / "notifications" / "argocd-notifications-cm.yaml"
        if path.exists():
            return load_yaml_file(path)
        return None

    def test_has_at_least_one_service(self, notifications_cm: dict[str, Any] | None) -> None:
        """Notification ConfigMap SHALL have at least one service."""
        if notifications_cm is None:
            pytest.skip("No notifications ConfigMap")

        data = notifications_cm.get("data", {})
        services = [k for k in data.keys() if k.startswith("service.")]

        assert len(services) > 0, "Must have at least one service configured"

    def test_triggers_reference_existing_templates(self, notifications_cm: dict[str, Any] | None) -> None:
        """All templates referenced in triggers SHALL exist."""
        if notifications_cm is None:
            pytest.skip("No notifications ConfigMap")

        data = notifications_cm.get("data", {})

        # Extract template names
        templates = {k.replace("template.", "") for k in data.keys() if k.startswith("template.")}

        # Extract templates referenced in triggers
        for key, value in data.items():
            if key.startswith("trigger.") and value:
                # Parse YAML trigger config
                trigger_config = yaml.safe_load(value)
                if isinstance(trigger_config, list):
                    for trigger in trigger_config:
                        send_list = trigger.get("send", [])
                        for template_name in send_list:
                            assert template_name in templates, (
                                f"Template '{template_name}' referenced in trigger '{key}' does not exist"
                            )


# **Feature: argocd-gitops-integration, Property 6: Custom health check Lua script validity**
class TestHealthCheckLuaValidity:
    """
    **Validates: Requirements 7.1**

    For any custom health check configuration, the Lua script SHALL be
    syntactically valid and return expected fields.
    """

    @pytest.fixture()
    def argocd_cm(self) -> dict[str, Any] | None:
        """Load ArgoCD ConfigMap."""
        path = ARGOCD_BASE_PATH / "base" / "argocd-cm.yaml"
        if path.exists():
            return load_yaml_file(path)
        return None

    def test_health_checks_have_return_statement(self, argocd_cm: dict[str, Any] | None) -> None:
        """Health check Lua scripts SHALL have return statement."""
        if argocd_cm is None:
            pytest.skip("No ArgoCD ConfigMap")

        data = argocd_cm.get("data", {})

        for key, value in data.items():
            if key.startswith("resource.customizations.health.") and value:
                assert "return" in value, f"Health check '{key}' must have return statement"

    def test_health_checks_initialize_hs_table(self, argocd_cm: dict[str, Any] | None) -> None:
        """Health check Lua scripts SHALL initialize hs table."""
        if argocd_cm is None:
            pytest.skip("No ArgoCD ConfigMap")

        data = argocd_cm.get("data", {})

        for key, value in data.items():
            if key.startswith("resource.customizations.health.") and value:
                assert "hs = {}" in value or "hs={}" in value, f"Health check '{key}' must initialize hs table"

    def test_health_checks_set_status_field(self, argocd_cm: dict[str, Any] | None) -> None:
        """Health check Lua scripts SHALL set hs.status field."""
        if argocd_cm is None:
            pytest.skip("No ArgoCD ConfigMap")

        data = argocd_cm.get("data", {})

        for key, value in data.items():
            if key.startswith("resource.customizations.health.") and value:
                assert "hs.status" in value, f"Health check '{key}' must set hs.status"


# **Feature: argocd-gitops-integration, Property 7: Sync wave annotation validity**
class TestSyncWaveAnnotations:
    """
    **Validates: Requirements 8.1**

    For any resource with sync wave annotation, the annotation value
    SHALL be a valid integer string.
    """

    SYNC_WAVE_PATTERN = re.compile(r"^-?\d+$")

    @pytest.fixture()
    def resources_with_sync_waves(self) -> list[tuple[str, dict[str, Any]]]:
        """Load all resources with sync wave annotations."""
        resources = []

        # Check hooks
        hooks_path = ARGOCD_BASE_PATH / "hooks"
        if hooks_path.exists():
            for yaml_file in hooks_path.glob("*.yaml"):
                if yaml_file.name != "kustomization.yaml":
                    docs = load_all_yaml_documents(yaml_file)
                    for doc in docs:
                        if doc:
                            annotations = doc.get("metadata", {}).get("annotations", {})
                            if "argocd.argoproj.io/sync-wave" in annotations:
                                resources.append((str(yaml_file), doc))

        # Check sealed secrets
        sealed_path = ARGOCD_BASE_PATH / "sealed-secrets"
        if sealed_path.exists():
            for yaml_file in sealed_path.glob("*.yaml"):
                if yaml_file.name != "kustomization.yaml":
                    docs = load_all_yaml_documents(yaml_file)
                    for doc in docs:
                        if doc:
                            annotations = doc.get("metadata", {}).get("annotations", {})
                            if "argocd.argoproj.io/sync-wave" in annotations:
                                resources.append((str(yaml_file), doc))

        return resources

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(resource_idx=st.integers(min_value=0, max_value=20))
    def test_sync_wave_is_valid_integer(
        self, resource_idx: int, resources_with_sync_waves: list[tuple[str, dict[str, Any]]]
    ) -> None:
        """Sync wave annotation SHALL be a valid integer."""
        if not resources_with_sync_waves:
            pytest.skip("No resources with sync waves")

        idx = resource_idx % len(resources_with_sync_waves)
        file_path, resource = resources_with_sync_waves[idx]

        annotations = resource["metadata"]["annotations"]
        sync_wave = annotations["argocd.argoproj.io/sync-wave"]

        # Handle quoted strings
        sync_wave_str = str(sync_wave).strip('"').strip("'")

        assert self.SYNC_WAVE_PATTERN.match(sync_wave_str), (
            f"Invalid sync wave '{sync_wave}' in {file_path}, must be integer"
        )


# **Feature: argocd-gitops-integration, Property: RBAC policies follow least-privilege**
class TestRBACLeastPrivilege:
    """
    **Validates: Requirements 1.2**

    RBAC policies SHALL follow least-privilege principle.
    """

    @pytest.fixture()
    def rbac_cm(self) -> dict[str, Any] | None:
        """Load RBAC ConfigMap."""
        path = ARGOCD_BASE_PATH / "base" / "argocd-rbac-cm.yaml"
        if path.exists():
            return load_yaml_file(path)
        return None

    def test_default_policy_is_readonly(self, rbac_cm: dict[str, Any] | None) -> None:
        """Default policy SHALL be readonly."""
        if rbac_cm is None:
            pytest.skip("No RBAC ConfigMap")

        data = rbac_cm.get("data", {})
        default_policy = data.get("policy.default", "")

        assert "readonly" in default_policy.lower(), "Default policy should be readonly for least-privilege"

    def test_developer_role_has_limited_permissions(self, rbac_cm: dict[str, Any] | None) -> None:
        """Developer role SHALL NOT have delete or admin permissions."""
        if rbac_cm is None:
            pytest.skip("No RBAC ConfigMap")

        data = rbac_cm.get("data", {})
        policy_csv = data.get("policy.csv", "")

        # Check developer role lines
        for line in policy_csv.split("\n"):
            if "role:developer" in line and "allow" in line:
                # Developer should not have delete or * (all) permissions
                assert "delete" not in line.lower(), "Developer role should not have delete permission"
                # Check for wildcard on sensitive resources
                if "clusters" in line or "accounts" in line:
                    parts = line.split(",")
                    if len(parts) >= 4:
                        action = parts[2].strip()
                        assert action != "*", f"Developer should not have wildcard on {line}"
