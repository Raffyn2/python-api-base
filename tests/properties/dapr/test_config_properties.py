"""Property-based tests for Dapr configuration.

These tests verify correctness properties for configuration management.
"""

from unittest.mock import patch

from hypothesis import given, settings, strategies as st

from core.config.infrastructure.dapr import DaprSettings


class TestConfigurationPriorityResolution:
    """
    **Feature: dapr-sidecar-integration, Property 30: Configuration Priority Resolution**
    **Validates: Requirements 12.4**

    For any configuration key present in multiple stores, the value from
    the highest-priority store should be returned.
    """

    @given(
        http_endpoint=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters=":/.-_"),
        ).filter(lambda x: x.strip()),
        grpc_endpoint=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters=":/.-_"),
        ).filter(lambda x: x.strip()),
        app_id=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_")
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, deadline=5000)
    def test_env_vars_override_defaults(
        self,
        http_endpoint: str,
        grpc_endpoint: str,
        app_id: str,
    ) -> None:
        """Environment variables should override default configuration values."""
        with patch.dict(
            "os.environ",
            {
                "DAPR_HTTP_ENDPOINT": http_endpoint,
                "DAPR_GRPC_ENDPOINT": grpc_endpoint,
                "DAPR_APP_ID": app_id,
            },
            clear=False,
        ):
            settings_obj = DaprSettings()

            assert settings_obj.http_endpoint == http_endpoint
            assert settings_obj.grpc_endpoint == grpc_endpoint
            assert settings_obj.app_id == app_id

    @given(
        enabled=st.booleans(),
        timeout=st.integers(min_value=1, max_value=3600),
    )
    @settings(max_examples=100, deadline=5000)
    def test_boolean_and_int_config_parsing(
        self,
        enabled: bool,
        timeout: int,
    ) -> None:
        """Boolean and integer configuration values should be parsed correctly."""
        with patch.dict(
            "os.environ",
            {
                "DAPR_ENABLED": str(enabled).lower(),
                "DAPR_TIMEOUT_SECONDS": str(timeout),
            },
            clear=False,
        ):
            settings_obj = DaprSettings()

            assert settings_obj.enabled == enabled
            assert settings_obj.timeout_seconds == timeout

    @given(
        api_token=st.one_of(
            st.none(),
            st.text(
                min_size=1,
                max_size=100,
                alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
            ).filter(lambda x: x.strip()),
        ),
    )
    @settings(max_examples=50, deadline=5000)
    def test_optional_config_values(
        self,
        api_token: str | None,
    ) -> None:
        """Optional configuration values should handle None correctly."""
        env_vars = {}
        if api_token is not None:
            env_vars["DAPR_API_TOKEN"] = api_token

        with patch.dict("os.environ", env_vars, clear=False):
            settings_obj = DaprSettings()

            if api_token is not None:
                assert settings_obj.api_token == api_token
            else:
                assert settings_obj.api_token is None

    @given(
        state_store=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_")
        ).filter(lambda x: x.strip()),
        pubsub_name=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_")
        ).filter(lambda x: x.strip()),
        secret_store=st.text(
            min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_")
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=50, deadline=5000)
    def test_component_name_configuration(
        self,
        state_store: str,
        pubsub_name: str,
        secret_store: str,
    ) -> None:
        """Component names should be configurable via environment variables."""
        with patch.dict(
            "os.environ",
            {
                "DAPR_STATE_STORE_NAME": state_store,
                "DAPR_PUBSUB_NAME": pubsub_name,
                "DAPR_SECRET_STORE_NAME": secret_store,
            },
            clear=False,
        ):
            settings_obj = DaprSettings()

            assert settings_obj.state_store_name == state_store
            assert settings_obj.pubsub_name == pubsub_name
            assert settings_obj.secret_store_name == secret_store
