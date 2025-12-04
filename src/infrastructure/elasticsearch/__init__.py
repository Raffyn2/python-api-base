"""Generic Elasticsearch infrastructure.

Provides type-safe Elasticsearch operations with PEP 695 generics.

**Feature: observability-infrastructure**
**Requirement: R2 - Generic Elasticsearch Client**
"""

from infrastructure.elasticsearch.client import ElasticsearchClient
from infrastructure.elasticsearch.config import ElasticsearchClientConfig
from infrastructure.elasticsearch.document import (
    DocumentMetadata,
    ElasticsearchDocument,
)
from infrastructure.elasticsearch.repository import (
    AggregationResult,
    ElasticsearchRepository,
    SearchQuery,
    SearchResult,
)

__all__ = [
    "AggregationResult",
    "DocumentMetadata",
    # Client
    "ElasticsearchClient",
    "ElasticsearchClientConfig",
    # Document
    "ElasticsearchDocument",
    # Repository
    "ElasticsearchRepository",
    "SearchQuery",
    "SearchResult",
]
