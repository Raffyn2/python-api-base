"""Security audit logger models.

**Feature: full-codebase-review-2025, Task 1.4: Refactor audit_logger**
**Validates: Requirements 9.2**

Models for security event logging with SIEM integration support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from infrastructure.security.audit_logger.enums import SecurityEventType, SecuritySeverity

# Default severity mapping for event types
EVENT_SEVERITY_MAP: dict[SecurityEventType, SecuritySeverity] = {
    SecurityEventType.AUTH_SUCCESS: SecuritySeverity.INFO,
    SecurityEventType.AUTH_FAILURE: SecuritySeverity.MEDIUM,
    SecurityEventType.MFA_FAILURE: SecuritySeverity.HIGH,
    SecurityEventType.TOKEN_ISSUED: SecuritySeverity.INFO,
    SecurityEventType.TOKEN_REVOKED: SecuritySeverity.LOW,
    SecurityEventType.TOKEN_REFRESH: SecuritySeverity.INFO,
    SecurityEventType.PASSWORD_CHANGE: SecuritySeverity.LOW,
    SecurityEventType.PASSWORD_RESET: SecuritySeverity.MEDIUM,
    SecurityEventType.AUTHZ_DENIED: SecuritySeverity.MEDIUM,
    SecurityEventType.PRIVILEGE_ESCALATION: SecuritySeverity.CRITICAL,
    SecurityEventType.ROLE_CHANGE: SecuritySeverity.MEDIUM,
    SecurityEventType.RATE_LIMIT_EXCEEDED: SecuritySeverity.LOW,
    SecurityEventType.SECRET_ACCESS: SecuritySeverity.MEDIUM,
    SecurityEventType.SECRET_ROTATION: SecuritySeverity.LOW,
    SecurityEventType.KEY_ROTATION: SecuritySeverity.LOW,
    SecurityEventType.SUSPICIOUS_ACTIVITY: SecuritySeverity.HIGH,
    SecurityEventType.CONFIG_CHANGE: SecuritySeverity.MEDIUM,
    SecurityEventType.DATA_EXPORT: SecuritySeverity.MEDIUM,
    SecurityEventType.DATA_DELETION: SecuritySeverity.HIGH,
}


def get_default_severity(event_type: SecurityEventType) -> SecuritySeverity:
    """Get default severity for an event type.

    Args:
        event_type: The security event type.

    Returns:
        Default severity level for the event type.
    """
    return EVENT_SEVERITY_MAP.get(event_type, SecuritySeverity.INFO)


@dataclass(frozen=True, slots=True)
class SecurityEvent:
    """Immutable security event record with correlation ID.

    **Feature: core-improvements-v2**
    **Validates: Requirements 4.5**

    Attributes:
        event_type: Type of security event.
        timestamp: When the event occurred (UTC).
        correlation_id: Request correlation ID for tracing.
        severity: Event severity for alerting.
        client_ip: Client IP address (may be redacted).
        user_id: User identifier (may be redacted).
        resource: Resource being accessed.
        action: Action being performed.
        reason: Reason for the event (e.g., failure reason).
        metadata: Additional context data.
    """

    event_type: SecurityEventType
    timestamp: datetime
    correlation_id: str
    severity: SecuritySeverity = SecuritySeverity.INFO
    client_ip: str | None = None
    user_id: str | None = None
    resource: str | None = None
    action: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for logging/SIEM."""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "client_ip": self.client_ip,
            "user_id": self.user_id,
            "resource": self.resource,
            "action": self.action,
            "reason": self.reason,
            **self.metadata,
        }

    def is_critical(self) -> bool:
        """Check if event requires immediate attention."""
        return self.severity in (SecuritySeverity.CRITICAL, SecuritySeverity.HIGH)
