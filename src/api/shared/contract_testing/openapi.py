"""OpenAPI contract validation.

**Feature: code-review-refactoring, Task 17.1: Refactor contract_testing.py**
**Validates: Requirements 5.4**
"""

import re
from typing import Any

from .contract import Contract, ContractInteraction


class OpenAPIContractValidator:
    """Validate contracts against OpenAPI specifications."""

    def __init__(self, openapi_spec: dict[str, Any]) -> None:
        """Initialize with OpenAPI spec."""
        self._spec = openapi_spec
        self._paths = openapi_spec.get("paths", {})

    def validate_interaction(
        self, interaction: ContractInteraction
    ) -> tuple[bool, list[str]]:
        """Validate interaction against OpenAPI spec."""
        errors: list[str] = []

        path_spec = self._find_path_spec(interaction.request_path)
        if path_spec is None:
            errors.append(
                f"Path '{interaction.request_path}' not found in OpenAPI spec"
            )
            return False, errors

        method_spec = path_spec.get(interaction.request_method.lower())
        if method_spec is None:
            errors.append(
                f"Method '{interaction.request_method}' not allowed for "
                f"path '{interaction.request_path}'"
            )
            return False, errors

        responses = method_spec.get("responses", {})
        status_str = str(interaction.expectation.status_code)
        if status_str not in responses and "default" not in responses:
            errors.append(
                f"Status code {interaction.expectation.status_code} not documented "
                f"for {interaction.request_method} {interaction.request_path}"
            )

        return len(errors) == 0, errors

    def _find_path_spec(self, path: str) -> dict[str, Any] | None:
        """Find path spec, handling path parameters."""
        if path in self._paths:
            return self._paths[path]

        for spec_path, spec in self._paths.items():
            pattern = re.sub(r"\{[^}]+\}", r"[^/]+", spec_path)
            if re.fullmatch(pattern, path):
                return spec

        return None

    def generate_contract_from_spec(
        self,
        consumer: str,
        provider: str,
        paths: list[str] | None = None,
    ) -> Contract:
        """Generate a contract from OpenAPI spec."""
        contract = Contract(
            name=f"{consumer}-{provider}-contract",
            consumer=consumer,
            provider=provider,
        )

        target_paths = paths or list(self._paths.keys())

        for path in target_paths:
            path_spec = self._paths.get(path, {})
            for method, method_spec in path_spec.items():
                if method in ["get", "post", "put", "patch", "delete"]:
                    responses = method_spec.get("responses", {})
                    for status in ["200", "201", "204"]:
                        if status in responses:
                            contract.add_interaction(
                                description=method_spec.get(
                                    "summary", f"{method.upper()} {path}"
                                ),
                                method=method.upper(),
                                path=path,
                                expected_status=int(status),
                            )
                            break

        return contract
