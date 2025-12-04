"""Generic RBAC infrastructure with PEP 695 type parameters.

**Feature: enterprise-generics-2025**
**Requirement: R14 - Generic RBAC System**

Exports:
    - Permission[TResource, TAction]: Generic permission
    - Role[TPermission]: Generic role
    - RBAC[TUser]: Generic RBAC checker
    - requires: Permission decorator
    - AuditEvent: Audit event model
"""

from infrastructure.rbac.audit import AuditEvent, AuditLogger, InMemoryAuditSink
from infrastructure.rbac.checker import RBAC, requires
from infrastructure.rbac.permission import Action, Permission, Resource
from infrastructure.rbac.role import Role, RoleRegistry

__all__ = [
    # RBAC
    "RBAC",
    "Action",
    # Audit
    "AuditEvent",
    "AuditLogger",
    "InMemoryAuditSink",
    # Permission
    "Permission",
    "Resource",
    # Role
    "Role",
    "RoleRegistry",
    "requires",
]
