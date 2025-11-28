"""Split protocols service.py into smaller modules."""

from pathlib import Path

# Read the file
path = Path("src/my_api/shared/protocols/service.py")
content = path.read_text()
lines = content.splitlines()

imports = '''"""Protocols base definitions.

Feature: file-size-compliance-phase2
"""

from abc import abstractmethod
from datetime import datetime
from typing import Any, Protocol, Sequence, runtime_checkable
from pydantic import BaseModel
'''

# Base protocols (lines 9-35)
base_content = imports + "\n\n" + "\n".join(lines[8:35])

# Repository protocols (lines 37-312)
repo_content = imports + "\n\n" + "\n".join(lines[36:312])

# Entity protocols (lines 314-415)
entity_content = imports + "\n\n" + "\n".join(lines[313:])

# Write files
pkg = Path("src/my_api/shared/protocols")
(pkg / "base.py").write_text(base_content)
(pkg / "repository.py").write_text(repo_content)
(pkg / "entities.py").write_text(entity_content)

# Remove old service.py
(pkg / "service.py").unlink()

# Update __init__.py
init_content = '''"""Protocol definitions for the application.

Feature: file-size-compliance-phase2
"""

from .base import Identifiable, SoftDeletable, Timestamped
from .entities import (
    Auditable,
    DeletableEntity,
    Entity,
    FullEntity,
    TrackedEntity,
    Versionable,
    VersionedEntity,
)
from .repository import (
    AsyncRepository,
    CacheProvider,
    Command,
    CommandHandler,
    EventHandler,
    Mapper,
    Query,
    QueryHandler,
    UnitOfWork,
)

__all__ = [
    "AsyncRepository",
    "Auditable",
    "CacheProvider",
    "Command",
    "CommandHandler",
    "DeletableEntity",
    "Entity",
    "EventHandler",
    "FullEntity",
    "Identifiable",
    "Mapper",
    "Query",
    "QueryHandler",
    "SoftDeletable",
    "Timestamped",
    "TrackedEntity",
    "UnitOfWork",
    "Versionable",
    "VersionedEntity",
]
'''
(pkg / "__init__.py").write_text(init_content)

print("OK: protocols split into base.py, repository.py, entities.py")
for f in pkg.glob("*.py"):
    print(f"  {f.name}: {len(f.read_text().splitlines())} lines")
