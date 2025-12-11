"""Security audit logger enums.

**Feature: full-codebase-review-2025, Task 1.4: Refactor audit_logger**
**Validates: Requirements 9.2**

Security Event Types aligned with OWASP Top 10 2025:
- A01: Broken Access Control (AUTHZ_DENIED, PRIVILEGE_ESCALATION)
- A02: Security Misconfiguration (CONFIG_CHANGE)
- A07: Authentication Failures (AUTH_FAILURE, MFA_FAILURE)
- A09: Logging Failures (covered by this module)
"""

from enum import Enum


class SecurityEventType(str, Enum):
    """Types of security events for audit logging.

    Categories:
        Authentication: AUTH_SUCCESS, AUTH_FAILURE, MFA_FAILURE, TOKEN_*
        Authorization: AUTHZ_DENIED, PRIVILEGE_ESCALATION
        Rate Limiting: RATE_LIMIT_EXCEEDED
        Secrets: SECRET_ACCESS, SECRET_ROTATION
        Security: SUSPICIOUS_ACTIVITY, CONFIG_CHANGE, DATA_EXPORT
    """

    # Authentication events
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"
    MFA_FAILURE = "MFA_FAILURE"
    TOKEN_ISSUED = "TOKEN_ISSUED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"

    # Authorization events
    AUTHZ_DENIED = "AUTHZ_DENIED"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    ROLE_CHANGE = "ROLE_CHANGE"

    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Secret management events
    SECRET_ACCESS = "SECRET_ACCESS"
    SECRET_ROTATION = "SECRET_ROTATION"
    KEY_ROTATION = "KEY_ROTATION"

    # Security events
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DELETION = "DATA_DELETION"


class SecuritySeverity(str, Enum):
    """Severity levels for security events.

    Used for alerting and prioritization in SIEM systems.
    """

    CRITICAL = "CRITICAL"  # Immediate action required
    HIGH = "HIGH"  # Investigate within 1 hour
    MEDIUM = "MEDIUM"  # Investigate within 24 hours
    LOW = "LOW"  # Review in regular audit
    INFO = "INFO"  # Informational only
