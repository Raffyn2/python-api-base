"""Knative manifest validator."""

from typing import Any, ClassVar

from infrastructure.eventing.knative.models import KnativeManifestError


class KnativeManifestValidator:
    """Validator for Knative Service manifests."""

    REQUIRED_FIELDS: ClassVar[list[str]] = ["apiVersion", "kind", "metadata", "spec"]
    REQUIRED_METADATA_FIELDS: ClassVar[list[str]] = ["name"]
    VALID_API_VERSIONS: ClassVar[list[str]] = [
        "serving.knative.dev/v1",
        "serving.knative.dev/v1beta1",
    ]
    VALID_AUTOSCALING_CLASSES: ClassVar[list[str]] = [
        "kpa.autoscaling.knative.dev",
        "hpa.autoscaling.knative.dev",
    ]
    VALID_AUTOSCALING_METRICS: ClassVar[list[str]] = ["concurrency", "rps", "cpu", "memory"]

    @classmethod
    def validate(cls, manifest: dict[str, Any]) -> list[str]:
        """Validate Knative Service manifest.

        Args:
            manifest: Manifest dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Check required fields
        errors.extend(f"Missing required field: {field}" for field in cls.REQUIRED_FIELDS if field not in manifest)

        if errors:
            return errors

        # Validate apiVersion
        api_version = manifest.get("apiVersion")
        if api_version not in cls.VALID_API_VERSIONS:
            errors.append(f"Invalid apiVersion: {api_version}")

        # Validate kind
        if manifest.get("kind") != "Service":
            errors.append(f"Invalid kind: {manifest.get('kind')}, expected 'Service'")

        # Validate metadata
        metadata = manifest.get("metadata", {})
        errors.extend(
            f"Missing required metadata field: {field}"
            for field in cls.REQUIRED_METADATA_FIELDS
            if field not in metadata
        )

        # Validate spec
        spec = manifest.get("spec", {})
        errors.extend(cls._validate_spec(spec))

        return errors

    @classmethod
    def _validate_spec(cls, spec: dict[str, Any]) -> list[str]:
        """Validate Knative Service spec.

        Args:
            spec: Spec dictionary to validate

        Returns:
            List of validation errors
        """
        errors: list[str] = []

        # Validate template
        template = spec.get("template", {})
        if not template:
            errors.append("Missing spec.template")
            return errors

        # Validate template spec
        template_spec = template.get("spec", {})
        errors.extend(cls._validate_template_spec(template_spec))

        # Validate annotations
        annotations = template.get("metadata", {}).get("annotations", {})
        errors.extend(cls._validate_annotations(annotations))

        # Validate traffic
        if "traffic" in spec:
            errors.extend(cls._validate_traffic(spec["traffic"]))

        return errors

    @classmethod
    def _validate_template_spec(cls, template_spec: dict[str, Any]) -> list[str]:
        """Validate template spec.

        Args:
            template_spec: Template spec dictionary

        Returns:
            List of validation errors
        """
        errors: list[str] = []

        # Validate containers
        containers = template_spec.get("containers", [])
        if not containers:
            errors.append("Missing spec.template.spec.containers")
            return errors

        container = containers[0]
        if "image" not in container:
            errors.append("Missing container image")

        # Validate containerConcurrency
        concurrency = template_spec.get("containerConcurrency", 0)
        if concurrency < 0:
            errors.append("containerConcurrency must be >= 0")

        # Validate timeoutSeconds
        timeout = template_spec.get("timeoutSeconds", 300)
        if timeout <= 0:
            errors.append("timeoutSeconds must be > 0")

        return errors

    @classmethod
    def _validate_annotations(cls, annotations: dict[str, str]) -> list[str]:
        """Validate autoscaling annotations.

        Args:
            annotations: Annotations dictionary

        Returns:
            List of validation errors
        """
        errors: list[str] = []
        cls._validate_autoscaling_class(annotations, errors)
        cls._validate_autoscaling_metric(annotations, errors)
        cls._validate_scale_values(annotations, errors)
        return errors

    @classmethod
    def _validate_autoscaling_class(cls, annotations: dict[str, str], errors: list[str]) -> None:
        """Validate autoscaling class annotation."""
        autoscaling_class = annotations.get("autoscaling.knative.dev/class")
        if autoscaling_class and autoscaling_class not in cls.VALID_AUTOSCALING_CLASSES:
            errors.append(f"Invalid autoscaling class: {autoscaling_class}")

    @classmethod
    def _validate_autoscaling_metric(cls, annotations: dict[str, str], errors: list[str]) -> None:
        """Validate autoscaling metric annotation."""
        autoscaling_metric = annotations.get("autoscaling.knative.dev/metric")
        if autoscaling_metric and autoscaling_metric not in cls.VALID_AUTOSCALING_METRICS:
            errors.append(f"Invalid autoscaling metric: {autoscaling_metric}")

    @classmethod
    def _validate_scale_values(cls, annotations: dict[str, str], errors: list[str]) -> None:
        """Validate min/max scale annotations."""
        min_scale = annotations.get("autoscaling.knative.dev/min-scale")
        max_scale = annotations.get("autoscaling.knative.dev/max-scale")

        min_val = cls._parse_scale_value(min_scale, "min-scale", errors)
        max_val = cls._parse_scale_value(max_scale, "max-scale", errors)

        if min_val is not None and max_val is not None and min_val > max_val:
            errors.append("min-scale must be <= max-scale")

    @classmethod
    def _parse_scale_value(cls, value: str | None, name: str, errors: list[str]) -> int | None:
        """Parse and validate a scale value."""
        if not value:
            return None
        try:
            parsed = int(value)
            if parsed < 0:
                errors.append(f"{name} must be >= 0")
            return parsed
        except ValueError:
            errors.append(f"Invalid {name} value: {value}")
            return None

    @classmethod
    def _validate_traffic(cls, traffic: list[dict[str, Any]]) -> list[str]:
        """Validate traffic configuration.

        Args:
            traffic: Traffic configuration list

        Returns:
            List of validation errors
        """
        errors: list[str] = []

        if not traffic:
            return errors

        total_percent = 0
        for target in traffic:
            percent = target.get("percent", 0)
            if percent < 0 or percent > 100:
                errors.append(f"Traffic percent must be between 0 and 100, got {percent}")
            total_percent += percent

            # Must have either revisionName or latestRevision
            if not target.get("revisionName") and not target.get("latestRevision"):
                errors.append("Traffic target must have revisionName or latestRevision")

        if total_percent != 100:
            errors.append(f"Traffic percentages must sum to 100, got {total_percent}")

        return errors

    @classmethod
    def is_valid(cls, manifest: dict[str, Any]) -> bool:
        """Check if manifest is valid.

        Args:
            manifest: Manifest dictionary

        Returns:
            True if valid, False otherwise
        """
        return len(cls.validate(manifest)) == 0

    @classmethod
    def validate_or_raise(cls, manifest: dict[str, Any]) -> None:
        """Validate manifest and raise exception if invalid.

        Args:
            manifest: Manifest dictionary

        Raises:
            KnativeManifestError: If manifest is invalid
        """
        errors = cls.validate(manifest)
        if errors:
            raise KnativeManifestError(f"Invalid manifest: {'; '.join(errors)}")
