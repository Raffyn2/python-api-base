#!/usr/bin/env python
"""Entity code generator for scaffolding new entities.

Usage:
    python scripts/generate_entity.py product
    python scripts/generate_entity.py order --fields "customer_id:str,total:float,status:str"
"""

import argparse
import re
from pathlib import Path
from textwrap import dedent


def to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def parse_fields(fields_str: str) -> list[tuple[str, str]]:
    """Parse field definitions from string.
    
    Args:
        fields_str: Comma-separated field:type pairs.
        
    Returns:
        List of (field_name, field_type) tuples.
    """
    if not fields_str:
        return []
    
    fields = []
    for field in fields_str.split(","):
        parts = field.strip().split(":")
        if len(parts) == 2:
            fields.append((parts[0].strip(), parts[1].strip()))
    return fields


def generate_entity(name: str, fields: list[tuple[str, str]]) -> str:
    """Generate entity file content."""
    pascal_name = to_pascal_case(name)
    
    field_defs = "\n    ".join(
        f'{fname}: {ftype} = SQLField(description="{fname.replace("_", " ").title()}")'
        for fname, ftype in fields
    ) if fields else 'name: str = SQLField(min_length=1, max_length=255, description="Name")'
    
    return dedent(f'''
        """{pascal_name} domain entity."""

        from datetime import datetime

        from sqlalchemy import Column, DateTime
        from sqlmodel import Field as SQLField
        from sqlmodel import SQLModel

        from my_api.shared.utils.ids import generate_ulid


        class {pascal_name}Base(SQLModel):
            """Base {name} fields shared between create/update/response."""

            {field_defs}


        class {pascal_name}({pascal_name}Base, table=True):
            """{ pascal_name} database model."""

            __tablename__ = "{name}s"

            id: str = SQLField(
                default_factory=generate_ulid,
                primary_key=True,
                description="ULID identifier",
            )
            created_at: datetime = SQLField(
                default_factory=lambda: datetime.now(),
                sa_column=Column(DateTime, nullable=False),
                description="Creation timestamp",
            )
            updated_at: datetime = SQLField(
                default_factory=lambda: datetime.now(),
                sa_column=Column(DateTime, nullable=False),
                description="Last update timestamp",
            )
            is_deleted: bool = SQLField(default=False, description="Soft delete flag")


        class {pascal_name}Create({pascal_name}Base):
            """DTO for creating {name}s."""
            pass


        class {pascal_name}Update(SQLModel):
            """DTO for updating {name}s (all fields optional)."""

            {"\n    ".join(f"{fname}: {ftype} | None = SQLField(default=None)" for fname, ftype in fields) if fields else "name: str | None = SQLField(default=None, min_length=1, max_length=255)"}


        class {pascal_name}Response({pascal_name}Base):
            """DTO for {name} responses."""

            id: str
            created_at: datetime
            updated_at: datetime

            model_config = {{"from_attributes": True}}
    ''').strip()


def generate_mapper(name: str) -> str:
    """Generate mapper file content."""
    pascal_name = to_pascal_case(name)
    
    return dedent(f'''
        """{pascal_name} mapper implementation."""

        from my_api.domain.entities.{name} import {pascal_name}, {pascal_name}Response
        from my_api.shared.mapper import BaseMapper


        class {pascal_name}Mapper(BaseMapper[{pascal_name}, {pascal_name}Response]):
            """Mapper for {pascal_name} entity to response DTO."""

            def __init__(self) -> None:
                """Initialize mapper."""
                super().__init__({pascal_name}, {pascal_name}Response)
    ''').strip()


def generate_use_case(name: str) -> str:
    """Generate use case file content."""
    pascal_name = to_pascal_case(name)
    
    return dedent(f'''
        """{pascal_name} use case implementation."""

        from my_api.domain.entities.{name} import (
            {pascal_name},
            {pascal_name}Create,
            {pascal_name}Response,
            {pascal_name}Update,
        )
        from my_api.shared.mapper import IMapper
        from my_api.shared.repository import IRepository
        from my_api.shared.use_case import BaseUseCase


        class {pascal_name}UseCase(
            BaseUseCase[{pascal_name}, {pascal_name}Create, {pascal_name}Update, {pascal_name}Response]
        ):
            """Use case for {pascal_name} operations."""

            def __init__(
                self,
                repository: IRepository[{pascal_name}, {pascal_name}Create, {pascal_name}Update],
                mapper: IMapper[{pascal_name}, {pascal_name}Response],
            ) -> None:
                """Initialize use case."""
                super().__init__(repository, mapper, entity_name="{pascal_name}")
    ''').strip()


def generate_routes(name: str) -> str:
    """Generate routes file content."""
    pascal_name = to_pascal_case(name)
    
    return dedent(f'''
        """{pascal_name} API routes."""

        from my_api.application.mappers.{name}_mapper import {pascal_name}Mapper
        from my_api.application.use_cases.{name}_use_case import {pascal_name}UseCase
        from my_api.domain.entities.{name} import (
            {pascal_name},
            {pascal_name}Create,
            {pascal_name}Response,
            {pascal_name}Update,
        )
        from my_api.shared.repository import InMemoryRepository
        from my_api.shared.router import GenericCRUDRouter


        # Singleton instances
        _{name}_mapper = {pascal_name}Mapper()
        _{name}_repository: InMemoryRepository[{pascal_name}, {pascal_name}Create, {pascal_name}Update] = (
            InMemoryRepository({pascal_name})
        )


        def get_{name}_use_case() -> {pascal_name}UseCase:
            """Dependency to get {pascal_name}UseCase."""
            return {pascal_name}UseCase(_{name}_repository, _{name}_mapper)


        # Create the generic CRUD router
        {name}_router = GenericCRUDRouter(
            prefix="/{name}s",
            tags=["{pascal_name}s"],
            response_model={pascal_name}Response,
            create_model={pascal_name}Create,
            update_model={pascal_name}Update,
            use_case_dependency=get_{name}_use_case,
        )

        router = {name}_router.router
    ''').strip()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate entity scaffolding")
    parser.add_argument("name", help="Entity name (snake_case)")
    parser.add_argument(
        "--fields",
        default="",
        help="Field definitions (e.g., 'name:str,price:float')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated code without writing files",
    )
    
    args = parser.parse_args()
    name = to_snake_case(args.name)
    fields = parse_fields(args.fields)
    
    # Define file paths
    base_path = Path(__file__).parent.parent / "src" / "my_api"
    files = {
        base_path / "domain" / "entities" / f"{name}.py": generate_entity(name, fields),
        base_path / "application" / "mappers" / f"{name}_mapper.py": generate_mapper(name),
        base_path / "application" / "use_cases" / f"{name}_use_case.py": generate_use_case(name),
        base_path / "adapters" / "api" / "routes" / f"{name}s.py": generate_routes(name),
    }
    
    for path, content in files.items():
        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"FILE: {path}")
            print("="*60)
            print(content)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                print(f"⚠️  Skipping {path} (already exists)")
            else:
                path.write_text(content)
                print(f"✓ Created {path}")
    
    if not args.dry_run:
        print(f"\n✓ Entity '{name}' scaffolding complete!")
        print(f"\nNext steps:")
        print(f"  1. Review generated files")
        print(f"  2. Add router to main.py:")
        print(f"     from my_api.adapters.api.routes import {name}s")
        print(f"     app.include_router({name}s.router, prefix='/api/v1')")
        print(f"  3. Create Alembic migration:")
        print(f"     python scripts/migrate.py revision -m 'add {name}s table'")


if __name__ == "__main__":
    main()
