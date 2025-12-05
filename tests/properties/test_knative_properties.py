"""Property-based tests for Knative serverless support.

Feature: knative-serverless-support
"""

import json
from datetime import datetime
from typing import Any

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from src.infrastructure.eventing.cloudevents.models import (
    CloudEvent,
    CloudEventValidationError,
)
from src.infrastructure.eventing.cloudevents.parser import CloudEventParser
from src.infrastructure.eventing.cloudevents.serializer import CloudEventSerializer
from src.infrastructure.eventing.knative.models import (
    KnativeServiceConfig,
    TrafficTarget,
    TrafficConfig,
    AutoscalingClass,
    AutoscalingMetric,
    InvalidTrafficConfigError,
)
from src.infrastructure.eventing.knative.generator import KnativeManifestGenerator
from src.infrastructure.eventing.knative.validator import KnativeManifestValidator


# Strategies for generating test data
resource_strategy = st.sampled_from(["100m", "200m", "500m", "1000m", "2000m"])
memory_strategy = st.sampled_from(["128Mi", "256Mi", "512Mi", "1Gi", "2Gi"])


@st.composite
def knative_service_config_strategy(draw: st.DrawFn) -> KnativeServiceConfig:
    """Strategy for generating valid KnativeServiceConfig."""
    min_scale = draw(st.integers(min_value=0, max_value=5))
    max_scale = draw(st.integers(min_value=min_scale, max_value=20))

    # Simplified name generation for faster tests
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=20))
    namespace = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=20))
    image = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=3, max_size=30))

    return KnativeServiceConfig(
        name=name,
        namespace=namespace,
        image=f"{image}:latest",
        port=draw(st.integers(min_value=1, max_value=65535)),
        autoscaling_class=draw(st.sampled_from(list(AutoscalingClass))),
        autoscaling_metric=draw(st.sampled_from(list(AutoscalingMetric))),
        autoscaling_target=draw(st.integers(min_value=1, max_value=1000)),
        min_scale=min_scale,
        max_scale=max_scale,
        scale_down_delay=draw(st.sampled_from(["15s", "30s", "60s", "120s"])),
        cpu_request=draw(resource_strategy),
        cpu_limit=draw(resource_strategy),
        memory_request=draw(memory_strategy),
        memory_limit=draw(memory_strategy),
        container_concurrency=draw(st.integers(min_value=0, max_value=1000)),
        timeout_seconds=draw(st.integers(min_value=1, max_value=900)),
        istio_sidecar=draw(st.booleans()),
    )


@st.composite
def traffic_targets_summing_to_100_strategy(draw: st.DrawFn) -> list[TrafficTarget]:
    """Strategy for generating traffic targets that sum to 100."""
    num_targets = draw(st.integers(min_value=1, max_value=5))

    if num_targets == 1:
        return [TrafficTarget(revision_name="rev-1", percent=100, tag="stable")]

    # Generate percentages that sum to 100
    percentages = []
    remaining = 100
    for i in range(num_targets - 1):
        max_percent = remaining - (num_targets - i - 1)
        if max_percent <= 0:
            percentages.append(0)
        else:
            p = draw(st.integers(min_value=0, max_value=max_percent))
            percentages.append(p)
            remaining -= p
    percentages.append(remaining)

    targets = []
    for i, percent in enumerate(percentages):
        targets.append(
            TrafficTarget(
                revision_name=f"rev-{i}",
                percent=percent,
                tag=f"tag-{i}" if draw(st.booleans()) else None,
            )
        )

    return targets


@st.composite
def traffic_targets_not_summing_to_100_strategy(draw: st.DrawFn) -> list[TrafficTarget]:
    """Strategy for generating traffic targets that don't sum to 100."""
    num_targets = draw(st.integers(min_value=1, max_value=5))
    total = draw(st.integers(min_value=0, max_value=200).filter(lambda x: x != 100))

    if num_targets == 1:
        percent = min(total, 100)
        return [TrafficTarget(revision_name="rev-1", percent=percent, tag="stable")]

    percentages = []
    remaining = total
    for i in range(num_targets - 1):
        max_percent = min(remaining, 100)
        if max_percent <= 0:
            percentages.append(0)
        else:
            p = draw(st.integers(min_value=0, max_value=max_percent))
            percentages.append(p)
            remaining -= p
    percentages.append(max(0, min(remaining, 100)))

    # Ensure total is not 100
    actual_total = sum(percentages)
    if actual_total == 100:
        percentages[0] = max(0, percentages[0] - 1)

    targets = []
    for i, percent in enumerate(percentages):
        targets.append(
            TrafficTarget(
                revision_name=f"rev-{i}",
                percent=percent,
            )
        )

    return targets


@st.composite
def valid_cloudevent_strategy(draw: st.DrawFn) -> CloudEvent:
    """Strategy for generating valid CloudEvents."""
    return CloudEvent(
        id=draw(st.uuids().map(str)),
        source=draw(st.text(min_size=1, max_size=100).map(lambda x: f"/{x}")),
        type=draw(st.text(min_size=1, max_size=100).map(lambda x: f"com.example.{x}")),
        specversion="1.0",
        datacontenttype=draw(st.sampled_from(["application/json", "text/plain", None])),
        subject=draw(st.text(min_size=0, max_size=50) | st.none()),
        time=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1)) | st.none()),
        data=draw(st.fixed_dictionaries({
            "key": st.text(min_size=1, max_size=20),
            "value": st.integers(),
        }) | st.none()),
    )


class TestKnativeManifestRoundTrip:
    """Property 1: Knative Service Manifest Round-Trip.

    **Feature: knative-serverless-support, Property 1: Knative Service Manifest Round-Trip**
    **Validates: Requirements 1.5, 2.5**
    """

    @given(config=knative_service_config_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_manifest_round_trip(self, config: KnativeServiceConfig) -> None:
        """For any valid KnativeServiceConfig, serializing to YAML and deserializing
        back should produce an equivalent configuration object.
        """
        # Serialize to YAML
        yaml_str = KnativeManifestGenerator.to_yaml(config)

        # Deserialize back
        parsed_config = KnativeManifestGenerator.from_yaml(yaml_str)

        # Check equivalence of key fields
        assert parsed_config.name == config.name
        assert parsed_config.namespace == config.namespace
        assert parsed_config.image == config.image
        assert parsed_config.port == config.port
        assert parsed_config.autoscaling_class == config.autoscaling_class
        assert parsed_config.autoscaling_metric == config.autoscaling_metric
        assert parsed_config.autoscaling_target == config.autoscaling_target
        assert parsed_config.min_scale == config.min_scale
        assert parsed_config.max_scale == config.max_scale
        assert parsed_config.container_concurrency == config.container_concurrency
        assert parsed_config.timeout_seconds == config.timeout_seconds


class TestTrafficPercentageValidation:
    """Property 2: Traffic Percentage Validation.

    **Feature: knative-serverless-support, Property 2: Traffic Percentage Validation**
    **Validates: Requirements 3.2, 3.5**
    """

    @given(targets=traffic_targets_summing_to_100_strategy())
    @settings(max_examples=100)
    def test_valid_traffic_config_accepted(self, targets: list[TrafficTarget]) -> None:
        """For any list of TrafficTarget objects where percentages sum to 100,
        validation should accept.
        """
        config = TrafficConfig(targets=targets)
        assert config.validate() is True

    @given(targets=traffic_targets_not_summing_to_100_strategy())
    @settings(max_examples=100)
    def test_invalid_traffic_config_rejected(self, targets: list[TrafficTarget]) -> None:
        """For any list of TrafficTarget objects where percentages don't sum to 100,
        validation should reject.
        """
        total = sum(t.percent for t in targets)
        assume(total != 100)

        with pytest.raises(InvalidTrafficConfigError):
            TrafficConfig(targets=targets)


class TestTrafficConfigurationGeneration:
    """Property 3: Traffic Configuration Generation.

    **Feature: knative-serverless-support, Property 3: Traffic Configuration Generation**
    **Validates: Requirements 3.1**
    """

    @given(targets=traffic_targets_summing_to_100_strategy())
    @settings(max_examples=100)
    def test_traffic_config_in_manifest(self, targets: list[TrafficTarget]) -> None:
        """For any valid TrafficConfig, the generated manifest should contain
        traffic entries matching the configuration.
        """
        traffic_config = TrafficConfig(targets=targets)

        config = KnativeServiceConfig(
            name="test-service",
            namespace="test-ns",
            image="test:latest",
            traffic=traffic_config,
        )

        manifest = KnativeManifestGenerator.generate(config)

        # Verify traffic is in manifest
        assert "traffic" in manifest["spec"]
        manifest_traffic = manifest["spec"]["traffic"]

        # Verify each target is present
        assert len(manifest_traffic) == len(targets)
        for i, target in enumerate(targets):
            assert manifest_traffic[i]["percent"] == target.percent
            if target.tag:
                assert manifest_traffic[i]["tag"] == target.tag


class TestAutoscalingAnnotationGeneration:
    """Property 9: Autoscaling Annotation Generation.

    **Feature: knative-serverless-support, Property 9: Autoscaling Annotation Generation**
    **Validates: Requirements 2.3**
    """

    @given(config=knative_service_config_strategy())
    @settings(max_examples=100)
    def test_autoscaling_annotations_generated(self, config: KnativeServiceConfig) -> None:
        """For any valid KnativeServiceConfig, the generated manifest should contain
        correct autoscaling annotations.
        """
        manifest = KnativeManifestGenerator.generate(config)

        annotations = manifest["spec"]["template"]["metadata"]["annotations"]

        assert annotations["autoscaling.knative.dev/class"] == config.autoscaling_class.value
        assert annotations["autoscaling.knative.dev/metric"] == config.autoscaling_metric.value
        assert annotations["autoscaling.knative.dev/target"] == str(config.autoscaling_target)
        assert annotations["autoscaling.knative.dev/min-scale"] == str(config.min_scale)
        assert annotations["autoscaling.knative.dev/max-scale"] == str(config.max_scale)


class TestCloudEventValidation:
    """Property 6: CloudEvent Validation.

    **Feature: knative-serverless-support, Property 6: CloudEvent Validation**
    **Validates: Requirements 10.2**
    """

    @given(event=valid_cloudevent_strategy())
    @settings(max_examples=100)
    def test_valid_cloudevent_accepted(self, event: CloudEvent) -> None:
        """For any CloudEvent with all required attributes, validation should accept."""
        event.validate()  # Should not raise

    @given(
        source=st.text(min_size=1, max_size=50),
        event_type=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100)
    def test_missing_id_rejected(self, source: str, event_type: str) -> None:
        """CloudEvent without id should be rejected."""
        with pytest.raises(CloudEventValidationError):
            CloudEvent(id="", source=source, type=event_type)

    @given(
        event_id=st.uuids().map(str),
        event_type=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100)
    def test_missing_source_rejected(self, event_id: str, event_type: str) -> None:
        """CloudEvent without source should be rejected."""
        with pytest.raises(CloudEventValidationError):
            CloudEvent(id=event_id, source="", type=event_type)

    @given(
        event_id=st.uuids().map(str),
        source=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=100)
    def test_missing_type_rejected(self, event_id: str, source: str) -> None:
        """CloudEvent without type should be rejected."""
        with pytest.raises(CloudEventValidationError):
            CloudEvent(id=event_id, source=source, type="")


class TestCloudEventRoundTrip:
    """Property 7: CloudEvent Round-Trip.

    **Feature: knative-serverless-support, Property 7: CloudEvent Round-Trip**
    **Validates: Requirements 8.5, 10.5**
    """

    @given(event=valid_cloudevent_strategy())
    @settings(max_examples=100)
    def test_structured_mode_round_trip(self, event: CloudEvent) -> None:
        """For any valid CloudEvent, serializing in structured mode and deserializing
        should produce an equivalent CloudEvent.
        """
        # Serialize
        headers, body = CloudEventSerializer.to_structured(event)

        # Deserialize
        parsed = CloudEventParser.parse_structured(body, headers["Content-Type"])

        # Check equivalence
        assert parsed.id == event.id
        assert parsed.source == event.source
        assert parsed.type == event.type
        assert parsed.specversion == event.specversion
        assert parsed.data == event.data

    @given(event=valid_cloudevent_strategy())
    @settings(max_examples=100)
    def test_binary_mode_round_trip(self, event: CloudEvent) -> None:
        """For any valid CloudEvent, serializing in binary mode and deserializing
        should produce an equivalent CloudEvent.
        """
        # Serialize
        headers, body = CloudEventSerializer.to_binary(event)

        # Deserialize
        parsed = CloudEventParser.parse_binary(headers, body)

        # Check equivalence
        assert parsed.id == event.id
        assert parsed.source == event.source
        assert parsed.type == event.type
        assert parsed.specversion == event.specversion


class TestCloudEventSerializationModes:
    """Property 8: CloudEvent Serialization Modes.

    **Feature: knative-serverless-support, Property 8: CloudEvent Serialization Modes**
    **Validates: Requirements 10.3**
    """

    @given(event=valid_cloudevent_strategy())
    @settings(max_examples=100)
    def test_both_modes_produce_valid_output(self, event: CloudEvent) -> None:
        """For any valid CloudEvent, both structured and binary serialization modes
        should produce valid output that can be deserialized.
        """
        # Structured mode
        structured_headers, structured_body = CloudEventSerializer.to_structured(event)
        assert "Content-Type" in structured_headers
        assert "application/cloudevents" in structured_headers["Content-Type"]
        assert len(structured_body) > 0

        # Binary mode
        binary_headers, binary_body = CloudEventSerializer.to_binary(event)
        assert "ce-id" in binary_headers
        assert "ce-source" in binary_headers
        assert "ce-type" in binary_headers
        assert "ce-specversion" in binary_headers

        # Both should be deserializable
        parsed_structured = CloudEventParser.parse_structured(
            structured_body, structured_headers["Content-Type"]
        )
        parsed_binary = CloudEventParser.parse_binary(binary_headers, binary_body)

        # Both should produce equivalent events
        assert parsed_structured.id == parsed_binary.id
        assert parsed_structured.source == parsed_binary.source
        assert parsed_structured.type == parsed_binary.type
