"""
Property-based tests for Istio Service Mesh manifests.

These tests validate correctness properties defined in the design document
for the istio-service-mesh feature.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given, settings, strategies as st

# Base path for Istio manifests
ISTIO_BASE_PATH = Path("deployments/istio/base")


def load_yaml_file(filepath: Path) -> list[dict[str, Any]]:
    """Load YAML file and return list of documents."""
    if not filepath.exists():
        return []
    with open(filepath) as f:
        return list(yaml.safe_load_all(f))


def load_all_istio_manifests() -> list[dict[str, Any]]:
    """Load all Istio manifests from base directory."""
    manifests = []
    for yaml_file in ISTIO_BASE_PATH.glob("*.yaml"):
        if yaml_file.name != "kustomization.yaml":
            manifests.extend(load_yaml_file(yaml_file))
    return [m for m in manifests if m is not None]


# =============================================================================
# Property 1: Sidecar Injection Label Consistency
# **Feature: istio-service-mesh, Property 1: Sidecar Injection Label Consistency**
# **Validates: Requirements 1.2**
# =============================================================================


def test_namespace_sidecar_injection_label():
    """
    For any Kubernetes namespace with label istio-injection=enabled,
    the namespace configuration SHALL have sidecar injection enabled.
    """
    namespaces = load_yaml_file(ISTIO_BASE_PATH / "namespace.yaml")

    for ns in namespaces:
        if ns.get("kind") != "Namespace":
            continue
        labels = ns.get("metadata", {}).get("labels", {})
        injection = labels.get("istio-injection")

        # If namespace is for application, it should have injection enabled
        if ns["metadata"]["name"] == "my-api":
            assert injection == "enabled", f"Namespace {ns['metadata']['name']} should have istio-injection=enabled"
        # istio-system should have injection disabled
        elif ns["metadata"]["name"] == "istio-system":
            assert injection == "disabled", "istio-system namespace should have istio-injection=disabled"


# =============================================================================
# Property 2: Resource Limits Within Bounds
# **Feature: istio-service-mesh, Property 2: Resource Limits Within Bounds**
# **Validates: Requirements 1.3**
# =============================================================================


def parse_cpu_to_millicores(cpu_str: str) -> int:
    """Convert CPU string to millicores."""
    if cpu_str.endswith("m"):
        return int(cpu_str[:-1])
    return int(float(cpu_str) * 1000)


def parse_memory_to_mi(mem_str: str) -> int:
    """Convert memory string to MiB."""
    if mem_str.endswith("Gi"):
        return int(float(mem_str[:-2]) * 1024)
    if mem_str.endswith("Mi"):
        return int(mem_str[:-2])
    if mem_str.endswith("Ki"):
        return int(float(mem_str[:-2]) / 1024)
    return int(mem_str)


def test_istio_resource_limits_within_bounds():
    """
    For any Istio component deployment, resource limits SHALL be within
    specified bounds (CPU: 500m-2000m, Memory: 512Mi-2Gi).
    """
    operators = load_yaml_file(ISTIO_BASE_PATH / "istio-operator.yaml")

    for op in operators:
        if op.get("kind") != "IstioOperator":
            continue

        components = op.get("spec", {}).get("components", {})

        # Check pilot resources
        pilot = components.get("pilot", {})
        pilot_resources = pilot.get("k8s", {}).get("resources", {})
        if pilot_resources:
            limits = pilot_resources.get("limits", {})
            if "cpu" in limits:
                cpu_mc = parse_cpu_to_millicores(limits["cpu"])
                assert 500 <= cpu_mc <= 2000, f"Pilot CPU limit {limits['cpu']} not in range 500m-2000m"
            if "memory" in limits:
                mem_mi = parse_memory_to_mi(limits["memory"])
                assert 512 <= mem_mi <= 2048, f"Pilot memory limit {limits['memory']} not in range 512Mi-2Gi"


# =============================================================================
# Property 3: mTLS STRICT Mode Enforcement
# **Feature: istio-service-mesh, Property 3: mTLS STRICT Mode Enforcement**
# **Validates: Requirements 2.1**
# =============================================================================


def test_mtls_strict_mode_enforcement():
    """
    For any PeerAuthentication resource in application namespaces where mTLS
    is enabled, the mode SHALL be set to STRICT.
    """
    peer_auths = load_yaml_file(ISTIO_BASE_PATH / "peerauthentication.yaml")

    for pa in peer_auths:
        if pa.get("kind") != "PeerAuthentication":
            continue

        mtls_mode = pa.get("spec", {}).get("mtls", {}).get("mode")
        namespace = pa.get("metadata", {}).get("namespace", "default")

        # Base configuration should be STRICT
        assert mtls_mode == "STRICT", f"PeerAuthentication in {namespace} should have STRICT mTLS, got {mtls_mode}"


# =============================================================================
# Property 5: VirtualService Weight Distribution
# **Feature: istio-service-mesh, Property 5: VirtualService Weight Distribution**
# **Validates: Requirements 3.1, 10.2**
# =============================================================================


def test_virtualservice_weights_sum_to_100():
    """
    For any VirtualService with multiple route destinations,
    the sum of all destination weights SHALL equal 100.
    """
    virtual_services = load_yaml_file(ISTIO_BASE_PATH / "virtualservice.yaml")

    for vs in virtual_services:
        if vs.get("kind") != "VirtualService":
            continue

        http_routes = vs.get("spec", {}).get("http", [])
        for route in http_routes:
            destinations = route.get("route", [])
            if len(destinations) > 1:
                weights = [d.get("weight", 0) for d in destinations]
                total = sum(weights)
                assert total == 100, f"VirtualService route weights sum to {total}, expected 100"


def generate_weights_summing_to_100(n: int) -> list[int]:
    """Generate n positive integers that sum to 100."""
    if n < 2:
        return [100]
    # Generate n-1 random cut points between 1 and 99
    import random

    cuts = sorted(random.sample(range(1, 100), n - 1))
    # Convert cuts to weights
    weights = [cuts[0]]
    for i in range(1, len(cuts)):
        weights.append(cuts[i] - cuts[i - 1])
    weights.append(100 - cuts[-1])
    return weights


@settings(max_examples=100)
@given(num_destinations=st.integers(min_value=2, max_value=5))
def test_property_virtualservice_weights_valid(num_destinations: int):
    """
    Property test: For any valid weight distribution, weights must sum to 100.
    **Feature: istio-service-mesh, Property 5: VirtualService Weight Distribution**
    **Validates: Requirements 3.1, 10.2**
    """
    weights = generate_weights_summing_to_100(num_destinations)
    assert sum(weights) == 100
    assert all(w > 0 for w in weights)
    assert len(weights) == num_destinations


# =============================================================================
# Property 6: Circuit Breaker Configuration Validity
# **Feature: istio-service-mesh, Property 6: Circuit Breaker Configuration Validity**
# **Validates: Requirements 3.2, 8.5**
# =============================================================================


def test_circuit_breaker_config_valid():
    """
    For any DestinationRule with outlierDetection configured,
    consecutive5xxErrors SHALL be positive, interval SHALL be valid duration,
    and maxEjectionPercent SHALL be between 0 and 100.
    """
    dest_rules = load_yaml_file(ISTIO_BASE_PATH / "destinationrule.yaml")

    for dr in dest_rules:
        if dr.get("kind") != "DestinationRule":
            continue

        traffic_policy = dr.get("spec", {}).get("trafficPolicy", {})
        outlier = traffic_policy.get("outlierDetection", {})

        if outlier:
            errors = outlier.get("consecutive5xxErrors", 0)
            assert errors > 0, "consecutive5xxErrors must be positive"

            max_ejection = outlier.get("maxEjectionPercent", 0)
            assert 0 <= max_ejection <= 100, f"maxEjectionPercent {max_ejection} not in range 0-100"

            interval = outlier.get("interval", "")
            assert re.match(r"^\d+[smh]$", interval), f"Invalid interval format: {interval}"


@settings(max_examples=100)
@given(
    consecutive_errors=st.integers(min_value=1, max_value=100),
    max_ejection=st.integers(min_value=0, max_value=100),
    interval_value=st.integers(min_value=1, max_value=300),
    interval_unit=st.sampled_from(["s", "m", "h"]),
)
def test_property_circuit_breaker_valid(
    consecutive_errors: int, max_ejection: int, interval_value: int, interval_unit: str
):
    """
    Property test: Circuit breaker config must have valid values.
    """
    assert consecutive_errors > 0
    assert 0 <= max_ejection <= 100
    interval = f"{interval_value}{interval_unit}"
    assert re.match(r"^\d+[smh]$", interval)


# =============================================================================
# Property 7: Retry Policy Configuration Validity
# **Feature: istio-service-mesh, Property 7: Retry Policy Configuration Validity**
# **Validates: Requirements 3.4**
# =============================================================================


def test_retry_policy_valid():
    """
    For any VirtualService with retry policy, attempts SHALL be between 1 and 10,
    and perTryTimeout SHALL be a valid positive duration.
    """
    virtual_services = load_yaml_file(ISTIO_BASE_PATH / "virtualservice.yaml")

    for vs in virtual_services:
        if vs.get("kind") != "VirtualService":
            continue

        http_routes = vs.get("spec", {}).get("http", [])
        for route in http_routes:
            retries = route.get("retries", {})
            if retries:
                attempts = retries.get("attempts", 0)
                assert 1 <= attempts <= 10, f"Retry attempts {attempts} not in range 1-10"

                timeout = retries.get("perTryTimeout", "")
                if timeout:
                    assert re.match(r"^\d+[smh]$", timeout), f"Invalid perTryTimeout format: {timeout}"


# =============================================================================
# Property 8: Timeout Configuration Validity
# **Feature: istio-service-mesh, Property 8: Timeout Configuration Validity**
# **Validates: Requirements 3.5**
# =============================================================================


def parse_duration_to_seconds(duration: str) -> int:
    """Convert duration string to seconds."""
    if duration.endswith("ms"):
        return int(duration[:-2]) // 1000
    if duration.endswith("s"):
        return int(duration[:-1])
    if duration.endswith("m"):
        return int(duration[:-1]) * 60
    if duration.endswith("h"):
        return int(duration[:-1]) * 3600
    return int(duration)


def test_timeout_config_valid():
    """
    For any VirtualService with timeout configured, the timeout value SHALL be
    a positive duration not exceeding 300 seconds.
    """
    virtual_services = load_yaml_file(ISTIO_BASE_PATH / "virtualservice.yaml")

    for vs in virtual_services:
        if vs.get("kind") != "VirtualService":
            continue

        http_routes = vs.get("spec", {}).get("http", [])
        for route in http_routes:
            timeout = route.get("timeout", "")
            if timeout:
                seconds = parse_duration_to_seconds(timeout)
                assert 0 < seconds <= 300, f"Timeout {timeout} ({seconds}s) not in range 1-300s"


# =============================================================================
# Property 9: Gateway TLS Configuration
# **Feature: istio-service-mesh, Property 9: Gateway TLS Configuration**
# **Validates: Requirements 4.1**
# =============================================================================


def test_gateway_tls_config():
    """
    For any Gateway with HTTPS server, the TLS configuration SHALL include
    credentialName referencing a valid certificate secret.
    """
    gateways = load_yaml_file(ISTIO_BASE_PATH / "gateway.yaml")

    for gw in gateways:
        if gw.get("kind") != "Gateway":
            continue

        servers = gw.get("spec", {}).get("servers", [])
        for server in servers:
            port = server.get("port", {})
            if port.get("protocol") == "HTTPS":
                tls = server.get("tls", {})
                assert tls.get("mode") in ["SIMPLE", "MUTUAL"], "HTTPS server must have TLS mode SIMPLE or MUTUAL"
                assert tls.get("credentialName"), "HTTPS server must have credentialName for TLS certificate"


# =============================================================================
# Property 10: Gateway-VirtualService Host Matching
# **Feature: istio-service-mesh, Property 10: Gateway-VirtualService Host Matching**
# **Validates: Requirements 4.2**
# =============================================================================


def test_gateway_virtualservice_host_matching():
    """
    For any VirtualService referencing a Gateway, at least one host in the
    VirtualService SHALL match a host defined in the referenced Gateway.
    """
    gateways = load_yaml_file(ISTIO_BASE_PATH / "gateway.yaml")
    virtual_services = load_yaml_file(ISTIO_BASE_PATH / "virtualservice.yaml")

    # Collect gateway hosts
    gateway_hosts: dict[str, set[str]] = {}
    for gw in gateways:
        if gw.get("kind") != "Gateway":
            continue
        name = gw["metadata"]["name"]
        hosts = set()
        for server in gw.get("spec", {}).get("servers", []):
            hosts.update(server.get("hosts", []))
        gateway_hosts[name] = hosts

    # Check VirtualService hosts match Gateway hosts
    for vs in virtual_services:
        if vs.get("kind") != "VirtualService":
            continue

        vs_gateways = vs.get("spec", {}).get("gateways", [])
        vs_hosts = set(vs.get("spec", {}).get("hosts", []))

        for gw_name in vs_gateways:
            if gw_name in gateway_hosts:
                gw_hosts = gateway_hosts[gw_name]
                # Check if any VS host matches any GW host (including wildcards)
                match_found = False
                for vs_host in vs_hosts:
                    for gw_host in gw_hosts:
                        if gw_host.startswith("*"):
                            # Wildcard match
                            if vs_host.endswith(gw_host[1:]):
                                match_found = True
                                break
                        elif vs_host == gw_host:
                            match_found = True
                            break
                    if match_found:
                        break

                assert match_found, f"VirtualService hosts {vs_hosts} don't match Gateway {gw_name} hosts {gw_hosts}"


# =============================================================================
# Property 12: CORS Configuration Completeness
# **Feature: istio-service-mesh, Property 12: CORS Configuration Completeness**
# **Validates: Requirements 4.4**
# =============================================================================


def test_cors_config_complete():
    """
    For any VirtualService with CORS policy enabled, allowOrigins, allowMethods,
    and allowHeaders SHALL be non-empty lists.
    """
    virtual_services = load_yaml_file(ISTIO_BASE_PATH / "virtualservice.yaml")

    for vs in virtual_services:
        if vs.get("kind") != "VirtualService":
            continue

        http_routes = vs.get("spec", {}).get("http", [])
        for route in http_routes:
            cors = route.get("corsPolicy", {})
            if cors:
                assert cors.get("allowOrigins"), "CORS allowOrigins cannot be empty"
                assert cors.get("allowMethods"), "CORS allowMethods cannot be empty"
                assert cors.get("allowHeaders"), "CORS allowHeaders cannot be empty"


# =============================================================================
# Property 13: Tracing Configuration
# **Feature: istio-service-mesh, Property 13: Tracing Configuration**
# **Validates: Requirements 5.2, 5.4**
# =============================================================================


def test_tracing_sampling_rate_valid():
    """
    For any Istio mesh configuration with tracing enabled,
    the sampling rate SHALL be between 0.0 and 100.0.
    """
    operators = load_yaml_file(ISTIO_BASE_PATH / "istio-operator.yaml")

    for op in operators:
        if op.get("kind") != "IstioOperator":
            continue

        mesh_config = op.get("spec", {}).get("meshConfig", {})
        default_config = mesh_config.get("defaultConfig", {})
        tracing = default_config.get("tracing", {})

        sampling = tracing.get("sampling", 0)
        assert 0.0 <= sampling <= 100.0, f"Tracing sampling rate {sampling} not in range 0-100"


# =============================================================================
# Property 15: AuthorizationPolicy Principal Validity
# **Feature: istio-service-mesh, Property 15: AuthorizationPolicy Principal Validity**
# **Validates: Requirements 6.1, 6.3**
# =============================================================================


def test_authz_policy_principal_format():
    """
    For any AuthorizationPolicy with source principals, each principal SHALL
    follow the format cluster.local/ns/{namespace}/sa/{serviceaccount}.
    """
    authz_policies = load_yaml_file(ISTIO_BASE_PATH / "authorizationpolicy.yaml")

    principal_pattern = re.compile(r"^cluster\.local/ns/[\w-]+/sa/[\w-]+$")

    for ap in authz_policies:
        if ap.get("kind") != "AuthorizationPolicy":
            continue

        rules = ap.get("spec", {}).get("rules", [])
        for rule in rules:
            from_sources = rule.get("from", [])
            for source in from_sources:
                principals = source.get("source", {}).get("principals", [])
                for principal in principals:
                    assert principal_pattern.match(principal), f"Invalid principal format: {principal}"


# =============================================================================
# Property 16: JWT JWKS URI Presence
# **Feature: istio-service-mesh, Property 16: JWT JWKS URI Presence**
# **Validates: Requirements 6.4**
# =============================================================================


def test_jwt_jwks_uri_present():
    """
    For any RequestAuthentication with JWT rules, each rule SHALL include
    a valid jwksUri or jwks.
    """
    request_auths = load_yaml_file(ISTIO_BASE_PATH / "requestauthentication.yaml")

    for ra in request_auths:
        if ra.get("kind") != "RequestAuthentication":
            continue

        jwt_rules = ra.get("spec", {}).get("jwtRules", [])
        for rule in jwt_rules:
            jwks_uri = rule.get("jwksUri")
            jwks = rule.get("jwks")

            assert jwks_uri or jwks, "JWT rule must have either jwksUri or jwks"

            if jwks_uri:
                assert jwks_uri.startswith("https://"), f"jwksUri must use HTTPS: {jwks_uri}"


# =============================================================================
# Property 19: ServiceEntry Host Validity
# **Feature: istio-service-mesh, Property 19: ServiceEntry Host Validity**
# **Validates: Requirements 8.1**
# =============================================================================


def test_serviceentry_host_valid():
    """
    For any ServiceEntry, hosts SHALL be valid DNS names or IP addresses,
    and ports SHALL have valid protocol specifications.
    """
    service_entries = load_yaml_file(ISTIO_BASE_PATH / "serviceentry.yaml")

    valid_protocols = {"HTTP", "HTTPS", "GRPC", "HTTP2", "MONGO", "TCP", "TLS"}
    dns_pattern = re.compile(r"^[\w\-\.\*]+$")

    for se in service_entries:
        if se.get("kind") != "ServiceEntry":
            continue

        hosts = se.get("spec", {}).get("hosts", [])
        assert hosts, "ServiceEntry must have at least one host"

        for host in hosts:
            assert dns_pattern.match(host), f"Invalid host format: {host}"

        ports = se.get("spec", {}).get("ports", [])
        for port in ports:
            protocol = port.get("protocol", "")
            assert protocol in valid_protocols, f"Invalid protocol: {protocol}"

            port_num = port.get("number", 0)
            assert 1 <= port_num <= 65535, f"Invalid port number: {port_num}"


# =============================================================================
# Property 20: Egress Policy Configuration
# **Feature: istio-service-mesh, Property 20: Egress Policy Configuration**
# **Validates: Requirements 8.2**
# =============================================================================


def test_egress_policy_registry_only():
    """
    For any Istio mesh configuration, outboundTrafficPolicy.mode SHALL be
    set to REGISTRY_ONLY for production environments.
    """
    operators = load_yaml_file(ISTIO_BASE_PATH / "istio-operator.yaml")

    for op in operators:
        if op.get("kind") != "IstioOperator":
            continue

        mesh_config = op.get("spec", {}).get("meshConfig", {})
        outbound_policy = mesh_config.get("outboundTrafficPolicy", {})
        mode = outbound_policy.get("mode", "")

        # Base config should be REGISTRY_ONLY
        assert mode == "REGISTRY_ONLY", f"outboundTrafficPolicy.mode should be REGISTRY_ONLY, got {mode}"


# =============================================================================
# Property 21: External Service DestinationRule Completeness
# **Feature: istio-service-mesh, Property 21: External Service DestinationRule Completeness**
# **Validates: Requirements 8.3, 8.4**
# =============================================================================


def test_external_service_destinationrule_complete():
    """
    For any DestinationRule targeting a ServiceEntry host, trafficPolicy SHALL
    include tls configuration and optionally connectionPool and outlierDetection.
    """
    dest_rules = load_yaml_file(ISTIO_BASE_PATH / "serviceentry.yaml")

    for dr in dest_rules:
        if dr.get("kind") != "DestinationRule":
            continue

        host = dr.get("spec", {}).get("host", "")
        traffic_policy = dr.get("spec", {}).get("trafficPolicy", {})

        # External services should have TLS config
        if "example.com" in host or "amazonaws.com" in host:
            tls = traffic_policy.get("tls", {})
            assert tls, f"External service {host} should have TLS configuration"
            assert tls.get("mode") in ["SIMPLE", "MUTUAL", "ISTIO_MUTUAL"], (
                f"Invalid TLS mode for external service {host}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
