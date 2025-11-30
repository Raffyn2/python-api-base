"""Contract definition.

**Feature: code-review-refactoring, Task 17.1: Refactor contract_testing.py**
**Validates: Requirements 5.4**
"""

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from .matchers import Matcher


@dataclass
class ContractExpectation:
    """Expected values for a contract interaction."""

    status_code: int = 200
    headers: dict[str, Matcher] = field(default_factory=dict)
    body_matchers: dict[str, Matcher] = field(default_factory=dict)
    body_schema: type[BaseModel] | None = None


@dataclass
class ContractInteraction:
    """A single interaction in a contract."""

    description: str
    request_method: str
    request_path: str
    request_headers: dict[str, str] = field(default_factory=dict)
    request_body: Any = None
    expectation: ContractExpectation = field(default_factory=ContractExpectation)


class Contract:
    """Definition of an API contract between consumer and provider."""

    def __init__(self, name: str, consumer: str, provider: str) -> None:
        """Initialize contract."""
        self.name = name
        self.consumer = consumer
        self.provider = provider
        self.interactions: list[ContractInteraction] = []
        self.metadata: dict[str, Any] = {}

    def add_interaction(
        self,
        description: str,
        method: str,
        path: str,
        request_headers: dict[str, str] | None = None,
        request_body: Any = None,
        expected_status: int = 200,
        expected_headers: dict[str, Matcher] | None = None,
        expected_body_matchers: dict[str, Matcher] | None = None,
        expected_body_schema: type[BaseModel] | None = None,
    ) -> "Contract":
        """Add an interaction to the contract."""
        expectation = ContractExpectation(
            status_code=expected_status,
            headers=expected_headers or {},
            body_matchers=expected_body_matchers or {},
            body_schema=expected_body_schema,
        )
        interaction = ContractInteraction(
            description=description,
            request_method=method.upper(),
            request_path=path,
            request_headers=request_headers or {},
            request_body=request_body,
            expectation=expectation,
        )
        self.interactions.append(interaction)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert contract to dictionary for serialization."""
        return {
            "name": self.name,
            "consumer": self.consumer,
            "provider": self.provider,
            "interactions": [
                {
                    "description": i.description,
                    "request": {
                        "method": i.request_method,
                        "path": i.request_path,
                        "headers": i.request_headers,
                        "body": i.request_body,
                    },
                    "response": {"status": i.expectation.status_code},
                }
                for i in self.interactions
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Contract":
        """Create contract from dictionary."""
        contract = cls(
            name=data["name"],
            consumer=data["consumer"],
            provider=data["provider"],
        )
        contract.metadata = data.get("metadata", {})
        for interaction_data in data.get("interactions", []):
            request = interaction_data.get("request", {})
            response = interaction_data.get("response", {})
            contract.add_interaction(
                description=interaction_data.get("description", ""),
                method=request.get("method", "GET"),
                path=request.get("path", "/"),
                request_headers=request.get("headers"),
                request_body=request.get("body"),
                expected_status=response.get("status", 200),
            )
        return contract
