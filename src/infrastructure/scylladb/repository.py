"""Generic ScyllaDB repository with PEP 695 generics.

**Feature: observability-infrastructure**
**Requirement: R4 - Generic ScyllaDB Repository**
**Security: Uses prepared statements to prevent CQL injection (S608)
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from infrastructure.scylladb.entity import ScyllaDBEntity

if TYPE_CHECKING:
    from uuid import UUID

    from infrastructure.scylladb.client import ScyllaDBClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=ScyllaDBEntity)

# Regex for valid CQL identifiers (table/column names)
_VALID_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_identifier(name: str, context: str = "identifier") -> str:
    """Validate CQL identifier to prevent injection.

    Args:
        name: Identifier to validate
        context: Context for error message

    Returns:
        Validated identifier

    Raises:
        ValueError: If identifier is invalid
    """
    if not name or not _VALID_IDENTIFIER.match(name):
        raise ValueError(f"Invalid CQL {context}: {name!r}")
    return name


class ScyllaDBRepository(Generic[T]):
    """Generic repository for ScyllaDB entities.

    Provides type-safe CRUD operations using PEP 695 generics pattern.

    **Feature: observability-infrastructure**
    **Requirement: R4.3 - Generic Repository**

    Example:
        >>> class User(ScyllaDBEntity):
        ...     __table_name__ = "users"
        ...     name: str
        ...     email: str
        >>> repo = ScyllaDBRepository[User](client, User)
        >>> user = await repo.create(User(name="John", email="john@ex.com"))
        >>> found = await repo.get(user.id)
    """

    def __init__(
        self,
        client: ScyllaDBClient,
        entity_class: type[T],
    ) -> None:
        """Initialize repository.

        Args:
            client: ScyllaDB client
            entity_class: Entity class for type conversion
        """
        self._client = client
        self._entity_class = entity_class
        self._prepared_statements: dict[str, Any] = {}

    @property
    def table_name(self) -> str:
        """Get validated table name."""
        return _validate_identifier(self._entity_class.table_name(), "table name")

    def _validate_columns(self, columns: list[str]) -> list[str]:
        """Validate column names."""
        return [_validate_identifier(col, "column name") for col in columns]

    async def _get_prepared(self, key: str, query: str) -> Any:
        """Get or create prepared statement.

        Args:
            key: Cache key for statement
            query: CQL query to prepare

        Returns:
            PreparedStatement
        """
        if key not in self._prepared_statements:
            self._prepared_statements[key] = await self._client.prepare(query)
        return self._prepared_statements[key]

    # CRUD Operations

    async def create(self, entity: T) -> T:
        """Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity
        """
        entity.updated_at = datetime.now(UTC)
        data = entity.to_dict()
        columns = self._validate_columns(list(data.keys()))
        placeholders = ", ".join(["%s"] * len(columns))
        cols_str = ", ".join(columns)

        stmt_key = f"insert_{self.table_name}"
        # S608: False positive - table/column names validated via _validate_identifier
        query = f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        await self._client.execute(prepared, tuple(data.values()))

        logger.debug(
            "Created entity in %s", self.table_name, extra={"id": str(entity.id)}
        )
        return entity

    async def get(self, id: UUID) -> T | None:
        """Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        pk_cols = self._validate_columns(self._entity_class.primary_key())
        where = " AND ".join(f"{col} = %s" for col in pk_cols)

        stmt_key = f"get_{self.table_name}"
        # S608: False positive - identifiers validated, uses prepared statement
        query = f"SELECT * FROM {self.table_name} WHERE {where}"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        rows = await self._client.execute(prepared, (id,))

        if not rows:
            return None

        return self._entity_class.from_row(rows[0])

    async def get_by_keys(self, **key_values: Any) -> T | None:
        """Get entity by composite key values.

        Args:
            **key_values: Key column values

        Returns:
            Entity or None if not found
        """
        columns = self._validate_columns(list(key_values.keys()))
        where_parts = [f"{col} = %s" for col in columns]
        values = list(key_values.values())

        where = " AND ".join(where_parts)
        stmt_key = f"get_by_keys_{self.table_name}_{'_'.join(columns)}"
        # S608: False positive - identifiers validated, uses prepared statement
        query = f"SELECT * FROM {self.table_name} WHERE {where}"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        rows = await self._client.execute(prepared, tuple(values))

        if not rows:
            return None

        return self._entity_class.from_row(rows[0])

    async def update(self, entity: T) -> T:
        """Update an entity.

        Args:
            entity: Entity with updated values

        Returns:
            Updated entity
        """
        entity.updated_at = datetime.now(UTC)
        data = entity.to_dict()

        # Separate PK from other columns
        pk_cols_raw = (
            self._entity_class.primary_key() + self._entity_class.clustering_key()
        )
        pk_cols = set(self._validate_columns(pk_cols_raw))
        update_cols = {k: v for k, v in data.items() if k not in pk_cols}
        pk_values = {k: v for k, v in data.items() if k in pk_cols}

        # Validate update columns
        validated_update_cols = self._validate_columns(list(update_cols.keys()))

        # Build SET clause
        set_parts = [f"{col} = %s" for col in validated_update_cols]
        set_clause = ", ".join(set_parts)

        # Build WHERE clause
        where_parts = [f"{col} = %s" for col in pk_cols]
        where_clause = " AND ".join(where_parts)

        stmt_key = f"update_{self.table_name}"
        # S608: False positive - identifiers validated, uses prepared statement
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        values = list(update_cols.values()) + [pk_values[col] for col in pk_cols]

        await self._client.execute(prepared, tuple(values))

        logger.debug(
            "Updated entity in %s", self.table_name, extra={"id": str(entity.id)}
        )
        return entity

    async def delete(self, id: UUID) -> bool:
        """Delete an entity.

        Args:
            id: Entity ID

        Returns:
            True if deleted
        """
        pk_cols = self._validate_columns(self._entity_class.primary_key())
        where = " AND ".join(f"{col} = %s" for col in pk_cols)

        stmt_key = f"delete_{self.table_name}"
        # S608: False positive - identifiers validated, uses prepared statement
        query = f"DELETE FROM {self.table_name} WHERE {where}"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        await self._client.execute(prepared, (id,))

        logger.debug("Deleted entity from %s", self.table_name, extra={"id": str(id)})
        return True

    async def delete_by_keys(self, **key_values: Any) -> bool:
        """Delete entity by composite key.

        Args:
            **key_values: Key column values

        Returns:
            True if deleted
        """
        columns = self._validate_columns(list(key_values.keys()))
        where_parts = [f"{col} = %s" for col in columns]
        values = list(key_values.values())

        where = " AND ".join(where_parts)
        stmt_key = f"delete_by_keys_{self.table_name}_{'_'.join(columns)}"
        # S608: False positive - identifiers validated, uses prepared statement
        query = f"DELETE FROM {self.table_name} WHERE {where}"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        await self._client.execute(prepared, tuple(values))
        return True

    async def exists(self, id: UUID) -> bool:
        """Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists
        """
        entity = await self.get(id)
        return entity is not None

    # Query Operations

    async def find_all(self, limit: int = 100) -> list[T]:
        """Find all entities.

        Args:
            limit: Maximum number to return

        Returns:
            List of entities
        """
        stmt_key = f"find_all_{self.table_name}"
        # S608: False positive - table name validated, uses prepared statement
        query = f"SELECT * FROM {self.table_name} LIMIT %s"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        rows = await self._client.execute(prepared, (limit,))

        return [self._entity_class.from_row(row) for row in rows]

    async def find_by(
        self,
        column: str,
        value: Any,
        limit: int = 100,
    ) -> list[T]:
        """Find entities by column value.

        Note: Column must be part of primary key or have an index.

        Args:
            column: Column name
            value: Column value
            limit: Maximum results

        Returns:
            List of matching entities
        """
        validated_col = _validate_identifier(column, "column name")
        stmt_key = f"find_by_{self.table_name}_{validated_col}"
        # S608: False positive - identifiers validated, uses prepared statement
        query = f"SELECT * FROM {self.table_name} WHERE {validated_col} = %s LIMIT %s"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        rows = await self._client.execute(prepared, (value, limit))

        return [self._entity_class.from_row(row) for row in rows]

    async def find_by_query(
        self,
        where_clause: str,
        values: tuple | None = None,
        limit: int = 100,
        allow_filtering: bool = False,
    ) -> list[T]:
        """Find entities by custom query.

        WARNING: where_clause must use parameterized placeholders (%s).
        Never interpolate user input directly into where_clause.

        Args:
            where_clause: WHERE clause with %s placeholders (without WHERE keyword)
            values: Parameter values matching placeholders
            limit: Maximum results
            allow_filtering: Add ALLOW FILTERING clause

        Returns:
            List of matching entities

        Raises:
            ValueError: If where_clause appears to contain injection attempts
        """
        # Basic injection detection (not foolproof, but catches obvious cases)
        dangerous_patterns = ["--", ";", "/*", "*/", "DROP", "TRUNCATE", "DELETE"]
        upper_clause = where_clause.upper()
        for pattern in dangerous_patterns:
            if pattern in upper_clause:
                raise ValueError(
                    f"Potentially dangerous pattern in where_clause: {pattern}"
                )

        # S608: Caller must ensure where_clause uses parameterized placeholders
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause} LIMIT %s"  # noqa: S608
        if allow_filtering:
            query += " ALLOW FILTERING"

        params = (*(values or ()), limit)
        rows = await self._client.execute(query, params)

        return [self._entity_class.from_row(row) for row in rows]

    async def count(self) -> int:
        """Count all entities.

        Returns:
            Entity count
        """
        stmt_key = f"count_{self.table_name}"
        # S608: False positive - table name validated, uses prepared statement
        query = f"SELECT COUNT(*) FROM {self.table_name}"  # noqa: S608
        prepared = await self._get_prepared(stmt_key, query)
        rows = await self._client.execute(prepared)

        return rows[0].count if rows else 0

    # Bulk Operations

    async def bulk_create(self, entities: list[T]) -> list[T]:
        """Bulk create entities.

        Args:
            entities: Entities to create

        Returns:
            Created entities
        """
        if not entities:
            return []

        statements = []
        for entity in entities:
            entity.updated_at = datetime.now(UTC)
            data = entity.to_dict()
            columns = self._validate_columns(list(data.keys()))
            placeholders = ", ".join(["%s"] * len(columns))
            cols_str = ", ".join(columns)

            # S608: False positive - identifiers validated via _validate_columns
            query = (
                f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholders})"  # noqa: S608
            )
            statements.append((query, tuple(data.values())))

        await self._client.execute_batch(statements, batch_type="UNLOGGED")

        logger.info("Bulk created %d entities in %s", len(entities), self.table_name)
        return entities

    async def bulk_delete(self, ids: list[UUID]) -> int:
        """Bulk delete entities.

        Args:
            ids: Entity IDs to delete

        Returns:
            Number deleted
        """
        if not ids:
            return 0

        pk_cols = self._validate_columns(self._entity_class.primary_key())
        where = " AND ".join(f"{col} = %s" for col in pk_cols)
        # S608: False positive - identifiers validated, parameterized query
        query = f"DELETE FROM {self.table_name} WHERE {where}"  # noqa: S608

        statements = [(query, (id,)) for id in ids]
        await self._client.execute_batch(statements, batch_type="UNLOGGED")

        logger.info("Bulk deleted %d entities from %s", len(ids), self.table_name)
        return len(ids)

    # Table Management

    async def ensure_table(self) -> bool:
        """Ensure table exists.

        Returns:
            True if created, False if existed
        """
        columns = self._entity_class.columns()
        pk = self._entity_class.primary_key()
        ck = self._entity_class.clustering_key()

        # Build primary key
        pk_def = f"({', '.join(pk)}), {', '.join(ck)}" if ck else ", ".join(pk)

        await self._client.create_table(
            table=self.table_name,
            columns=columns,
            primary_key=pk_def,
            if_not_exists=True,
        )

        return True

    async def truncate(self) -> None:
        """Truncate the table."""
        await self._client.truncate_table(self.table_name)
