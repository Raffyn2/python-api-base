"""Tests for core/base/cqrs/query.py - Base Query class."""

from dataclasses import dataclass
from datetime import datetime

import pytest

from src.core.base.cqrs.query import BaseQuery


@dataclass(frozen=True)
class GetUserQuery(BaseQuery[dict]):
    """Test query for getting a user."""

    user_id: str = ""


@dataclass(frozen=True)
class ListItemsQuery(BaseQuery[list]):
    """Test query for listing items."""

    page: int = 1
    size: int = 20


class TestBaseQueryInit:
    """Tests for BaseQuery initialization."""

    def test_query_has_auto_generated_id(self):
        query = GetUserQuery(user_id="user-123")
        assert query.query_id is not None
        assert len(query.query_id) > 0

    def test_query_has_timestamp(self):
        query = GetUserQuery(user_id="user-123")
        assert query.timestamp is not None
        assert isinstance(query.timestamp, datetime)

    def test_query_id_is_unique(self):
        query1 = GetUserQuery(user_id="user-1")
        query2 = GetUserQuery(user_id="user-2")
        assert query1.query_id != query2.query_id

    def test_correlation_id_default_none(self):
        query = GetUserQuery(user_id="user-123")
        assert query.correlation_id is None

    def test_cache_key_default_none(self):
        query = GetUserQuery(user_id="user-123")
        assert query.cache_key is None

    def test_cache_ttl_default_none(self):
        query = GetUserQuery(user_id="user-123")
        assert query.cache_ttl is None

    def test_custom_correlation_id(self):
        query = GetUserQuery(user_id="user-123", correlation_id="corr-456")
        assert query.correlation_id == "corr-456"

    def test_custom_cache_key(self):
        query = GetUserQuery(user_id="user-123", cache_key="user:123")
        assert query.cache_key == "user:123"

    def test_custom_cache_ttl(self):
        query = GetUserQuery(user_id="user-123", cache_ttl=300)
        assert query.cache_ttl == 300

    def test_custom_query_id(self):
        query = GetUserQuery(user_id="user-123", query_id="custom-query-id")
        assert query.query_id == "custom-query-id"


class TestBaseQueryImmutability:
    """Tests for BaseQuery immutability."""

    def test_query_is_frozen(self):
        query = GetUserQuery(user_id="user-123")
        with pytest.raises(AttributeError):
            query.user_id = "changed"

    def test_query_id_is_frozen(self):
        query = GetUserQuery(user_id="user-123")
        with pytest.raises(AttributeError):
            query.query_id = "new-id"


class TestBaseQueryType:
    """Tests for query_type property."""

    def test_query_type_returns_class_name(self):
        query = GetUserQuery(user_id="user-123")
        assert query.query_type == "GetUserQuery"

    def test_different_query_types(self):
        get_query = GetUserQuery(user_id="user-123")
        list_query = ListItemsQuery(page=1, size=10)
        assert get_query.query_type == "GetUserQuery"
        assert list_query.query_type == "ListItemsQuery"


class TestBaseQueryGetCacheKey:
    """Tests for get_cache_key method."""

    def test_get_cache_key_uses_custom_key(self):
        query = GetUserQuery(user_id="user-123", cache_key="custom:key")
        assert query.get_cache_key() == "custom:key"

    def test_get_cache_key_generates_default(self):
        query = GetUserQuery(user_id="user-123", query_id="q-123")
        assert query.get_cache_key() == "GetUserQuery:q-123"

    def test_get_cache_key_includes_query_type(self):
        query = ListItemsQuery(page=1, size=10, query_id="list-q")
        cache_key = query.get_cache_key()
        assert "ListItemsQuery" in cache_key

    def test_get_cache_key_includes_query_id(self):
        query = GetUserQuery(user_id="user-123", query_id="specific-id")
        cache_key = query.get_cache_key()
        assert "specific-id" in cache_key


class TestBaseQueryToDict:
    """Tests for to_dict method."""

    def test_to_dict_returns_dict(self):
        query = GetUserQuery(user_id="user-123")
        result = query.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_user_id(self):
        query = GetUserQuery(user_id="user-456")
        result = query.to_dict()
        assert result["user_id"] == "user-456"

    def test_to_dict_contains_query_id(self):
        query = GetUserQuery(user_id="user-123", query_id="q-789")
        result = query.to_dict()
        assert result["query_id"] == "q-789"

    def test_to_dict_contains_timestamp(self):
        query = GetUserQuery(user_id="user-123")
        result = query.to_dict()
        assert "timestamp" in result
        assert isinstance(result["timestamp"], datetime)

    def test_to_dict_contains_correlation_id(self):
        query = GetUserQuery(user_id="user-123", correlation_id="corr-abc")
        result = query.to_dict()
        assert result["correlation_id"] == "corr-abc"

    def test_to_dict_contains_cache_key(self):
        query = GetUserQuery(user_id="user-123", cache_key="cache:key")
        result = query.to_dict()
        assert result["cache_key"] == "cache:key"

    def test_to_dict_contains_cache_ttl(self):
        query = GetUserQuery(user_id="user-123", cache_ttl=600)
        result = query.to_dict()
        assert result["cache_ttl"] == 600


class TestListItemsQuery:
    """Tests for ListItemsQuery."""

    def test_list_query_has_page(self):
        query = ListItemsQuery(page=2, size=20)
        assert query.page == 2

    def test_list_query_has_size(self):
        query = ListItemsQuery(page=1, size=50)
        assert query.size == 50

    def test_list_query_default_values(self):
        query = ListItemsQuery()
        assert query.page == 1
        assert query.size == 20

    def test_list_query_type(self):
        query = ListItemsQuery(page=1, size=10)
        assert query.query_type == "ListItemsQuery"

    def test_list_query_to_dict(self):
        query = ListItemsQuery(page=3, size=25)
        result = query.to_dict()
        assert result["page"] == 3
        assert result["size"] == 25


class TestBaseQueryEquality:
    """Tests for query equality."""

    def test_same_query_id_equals(self):
        query1 = GetUserQuery(user_id="user-123", query_id="same-id")
        query2 = GetUserQuery(user_id="user-123", query_id="same-id")
        assert query1.query_id == query2.query_id

    def test_different_query_ids_not_equal(self):
        query1 = GetUserQuery(user_id="user-123")
        query2 = GetUserQuery(user_id="user-123")
        assert query1.query_id != query2.query_id
