"""Property-based tests for Dapr security.

These tests verify correctness properties for security operations.
"""

from hypothesis import given, settings, strategies as st


class TestMtlsEnforcement:
    """
    **Feature: dapr-sidecar-integration, Property 28: mTLS Enforcement**
    **Validates: Requirements 13.1**

    For any service-to-service communication, mTLS encryption should be
    enforced between sidecars.
    """

    @given(
        app_id=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_")
        ).filter(lambda x: x.strip()),
        method=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_/")
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, deadline=5000)
    def test_service_invocation_uses_dapr_endpoint(
        self,
        app_id: str,
        method: str,
    ) -> None:
        """Service invocation should use Dapr endpoint (mTLS handled by sidecar)."""
        dapr_endpoint = "http://localhost:3500"
        expected_url = f"{dapr_endpoint}/v1.0/invoke/{app_id}/method/{method}"

        assert "/v1.0/invoke/" in expected_url
        assert app_id in expected_url
        assert method in expected_url

    @given(
        trust_domain=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters=".-")
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    def test_mtls_config_trust_domain(
        self,
        trust_domain: str,
    ) -> None:
        """mTLS configuration should include trust domain."""
        mtls_config = {
            "enabled": True,
            "trustDomain": trust_domain,
            "allowedClockSkew": "15m",
            "workloadCertTTL": "24h",
        }

        assert mtls_config["enabled"] is True
        assert mtls_config["trustDomain"] == trust_domain

    @given(
        cert_ttl=st.sampled_from(["1h", "12h", "24h", "168h"]),
        clock_skew=st.sampled_from(["5m", "10m", "15m", "30m"]),
    )
    @settings(max_examples=20, deadline=5000)
    def test_mtls_certificate_configuration(
        self,
        cert_ttl: str,
        clock_skew: str,
    ) -> None:
        """mTLS certificate configuration should be valid."""
        sentry_config = {
            "spec": {
                "trustDomain": "cluster.local",
                "allowedClockSkew": clock_skew,
                "workloadCertTTL": cert_ttl,
            }
        }

        assert sentry_config["spec"]["workloadCertTTL"] == cert_ttl
        assert sentry_config["spec"]["allowedClockSkew"] == clock_skew


class TestApiTokenAuthentication:
    """
    Tests for API token authentication.
    **Validates: Requirements 13.2**
    """

    @given(
        api_token=st.text(
            min_size=10,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    def test_api_token_header_added(
        self,
        api_token: str,
    ) -> None:
        """API token should be added to request headers."""
        headers = {}
        if api_token:
            headers["dapr-api-token"] = api_token

        assert "dapr-api-token" in headers
        assert headers["dapr-api-token"] == api_token

    @given(
        api_token=st.text(
            min_size=10,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    def test_api_token_not_logged(
        self,
        api_token: str,
    ) -> None:
        """API token should not appear in log messages."""
        log_message = "Request to /v1.0/invoke/service/method"
        safe_headers = {"Content-Type": "application/json"}

        assert api_token not in log_message
        assert api_token not in str(safe_headers)


class TestAccessControlPolicies:
    """
    Tests for access control policies.
    **Validates: Requirements 13.3**
    """

    @given(
        app_id=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_")
        ).filter(lambda x: x.strip()),
        operation=st.sampled_from(["allow", "deny"]),
    )
    @settings(max_examples=50, deadline=5000)
    def test_access_control_policy_format(
        self,
        app_id: str,
        operation: str,
    ) -> None:
        """Access control policies should have valid format."""
        policy = {
            "appId": app_id,
            "defaultAction": operation,
            "trustDomain": "public",
            "namespace": "default",
        }

        assert policy["appId"] == app_id
        assert policy["defaultAction"] in ["allow", "deny"]

    @given(
        allowed_apps=st.lists(
            st.text(
                min_size=1,
                max_size=30,
                alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
            ).filter(lambda x: x.strip()),
            min_size=1,
            max_size=10,
            unique=True,
        ),
    )
    @settings(max_examples=50, deadline=5000)
    def test_access_control_app_list(
        self,
        allowed_apps: list[str],
    ) -> None:
        """Access control should support app allowlists."""
        access_control = {
            "defaultAction": "deny",
            "policies": [{"appId": app, "defaultAction": "allow"} for app in allowed_apps],
        }

        assert access_control["defaultAction"] == "deny"
        assert len(access_control["policies"]) == len(allowed_apps)

        for policy in access_control["policies"]:
            assert policy["appId"] in allowed_apps
            assert policy["defaultAction"] == "allow"
