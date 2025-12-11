"""Security audit logging for authentication and authorization events.

**Feature: code-review-refactoring, Task 13.1: Create SecurityAuditLogger**
**Validates: Requirements 10.4, 10.5**

Provides specialized security event logging with:
- PII redaction for GDPR/CCPA compliance
- Severity levels for SIEM integration
- Correlation ID tracking for distributed tracing
- OWASP Top 10 2025 aligned event types

Example:
    >>> from infrastructure.security.audit_logger import (
    ...     SecurityAuditLogger,
    ...     get_audit_logger,
    ... )
    >>> logger = get_audit_logger()
    >>> logger.log_auth_success(user_id="user123", client_ip="1.2.3.4", method="oauth2")
"""

from infrastructure.security.audit_logger.enums import SecurityEventType, SecuritySeverity
from infrastructure.security.audit_logger.models import (
    EVENT_SEVERITY_MAP,
    SecurityEvent,
    get_default_severity,
)
from infrastructure.security.audit_logger.patterns import IP_PATTERNS, PII_PATTERNS
from infrastructure.security.audit_logger.service import (
    SecurityAuditLogger,
    get_audit_logger,
)

__all__ = [
    "EVENT_SEVERITY_MAP",
    "IP_PATTERNS",
    "PII_PATTERNS",
    "SecurityAuditLogger",
    "SecurityEvent",
    "SecurityEventType",
    "SecuritySeverity",
    "get_audit_logger",
    "get_default_severity",
]
