"""Test factories for generating test data."""

from tests.factories.generic_fixtures import (
    MapperTestCase,
    RepositoryTestCase,
    TestContext,
    UseCaseTestCase,
    create_in_memory_repository,
    create_test_context,
)
from tests.factories.hypothesis_strategies import (
    create_dto_strategy,
    create_model_strategy,
    datetime_strategy,
    email_strategy,
    entity_strategy,
    list_of,
    one_of_models,
    optional,
    page_number_strategy,
    page_size_strategy,
    pydantic_strategy,
    strategy_for_field,
    ulid_strategy,
    update_dto_strategy,
    uuid_strategy,
)
from tests.factories.mock_repository import (
    CallRecord,
    MethodCallTracker,
    MockRepository,
    MockRepositoryFactory,
    TypedMock,
    create_typed_mock,
)

__all__ = [
    "CallRecord",
    # Generic Test Fixtures
    "MapperTestCase",
    "MethodCallTracker",
    # Mock Repository
    "MockRepository",
    "MockRepositoryFactory",
    "RepositoryTestCase",
    "TestContext",
    # Type-safe Mocks
    "TypedMock",
    "UseCaseTestCase",
    "create_dto_strategy",
    "create_in_memory_repository",
    "create_model_strategy",
    "create_test_context",
    "create_typed_mock",
    "datetime_strategy",
    "email_strategy",
    "entity_strategy",
    "list_of",
    "one_of_models",
    "optional",
    "page_number_strategy",
    "page_size_strategy",
    # Hypothesis Strategies
    "pydantic_strategy",
    "strategy_for_field",
    "ulid_strategy",
    "update_dto_strategy",
    "uuid_strategy",
]
