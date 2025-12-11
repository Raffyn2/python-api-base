"""Security audit logger service.

**Feature: full-codebase-review-2025, Task 1.4: Refactor audit_logger**
**Validates: Requirements 9.2**

This module provides specialized security event logging with:
- PII redaction for compliance (GDPR, CCPA)
- Correlation ID tracking for distributed tracing
- Structured logging for SIEM integration
- Optional integration with generic audit backend

For generic CRUD audit logging, see `infrastructure.security.audit.log`.
"""

import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from core.shared.utils.ids import generate_ulid
from infrastructure.security.audit_logger.enums import SecurityEventType, SecuritySeverity
from infrastructure.security.audit_logger.models import SecurityEvent, get_default_severity
from infrastructure.security.audit_logger.patterns import IP_PATTERNS, PII_PATTERNS

if TYPE_CHECKING:
    from infrastructure.security.audit.log import AuditLogger


class SecurityAuditLogger:
    """Log security-relevant events for audit trail.

    **Feature: code-review-refactoring, Property 14: Audit Log Completeness**
    **Validates: Requirements 10.4, 10.5**
    """

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger | None = None,
        redact_pii: bool = True,
        correlation_id_provider: Callable[[], str] | None = None,
        redact_ip_addresses: bool = False,
        audit_backend: "AuditLogger | None" = None,
    ) -> None:
        """Initialize security audit logger.

        Args:
            logger: Structlog logger instance.
            redact_pii: Whether to redact PII from log messages.
            correlation_id_provider: Function to generate correlation IDs.
            redact_ip_addresses: Whether to redact IP addresses.
            audit_backend: Optional generic audit logger for persistence.
        """
        self._logger = logger or structlog.get_logger("security.audit")
        self._redact_pii = redact_pii
        self._get_correlation_id = correlation_id_provider or generate_ulid
        self._redact_ip = redact_ip_addresses
        self._audit_backend = audit_backend

    def _redact(self, value: str | None) -> str | None:
        """Redact PII from a string value."""
        if not value or not self._redact_pii:
            return value
        result = value
        for pattern, replacement in PII_PATTERNS:
            result = pattern.sub(replacement, result)
        if self._redact_ip:
            for pattern, replacement in IP_PATTERNS:
                result = pattern.sub(replacement, result)
        return result

    def _create_event(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity | None = None,
        **kwargs: Any,
    ) -> SecurityEvent:
        """Create a security event with current timestamp and correlation ID.

        Args:
            event_type: Type of security event.
            severity: Override default severity (optional).
            **kwargs: Additional event attributes.

        Returns:
            SecurityEvent instance.
        """
        return SecurityEvent(
            event_type=event_type,
            timestamp=datetime.now(UTC),
            correlation_id=self._get_correlation_id(),
            severity=severity or get_default_severity(event_type),
            **kwargs,
        )

    async def _persist_to_backend(self, event: SecurityEvent) -> None:
        """Persist event to audit backend if configured.

        Args:
            event: Security event to persist.
        """
        if self._audit_backend is None:
            return

        try:
            from infrastructure.security.audit.log import AuditEntry

            # Map security event to generic audit entry
            result = "success" if "SUCCESS" in event.event_type.value else "failure"
            entry = AuditEntry(
                id=event.correlation_id,
                timestamp=event.timestamp,
                action=event.event_type.value,
                resource_type="security",
                result=result,
                user_id=event.user_id,
                resource_id=event.resource,
                details=event.metadata,
                ip_address=event.client_ip,
            )
            await self._audit_backend.log(entry)
        except Exception:
            self._logger.exception(
                "Failed to persist to audit backend",
                operation="AUDIT_PERSIST_ERROR",
                event_type=event.event_type.value,
            )

    def log_auth_success(
        self,
        user_id: str,
        client_ip: str,
        method: str,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log successful authentication."""
        event = self._create_event(
            SecurityEventType.AUTH_SUCCESS,
            user_id=user_id,
            client_ip=client_ip,
            action=method,
            metadata=metadata or {},
        )
        self._logger.info("Authentication successful", extra=event.to_dict())
        return event

    def log_auth_failure(
        self,
        client_ip: str,
        reason: str,
        attempted_user: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log failed authentication attempt."""
        event = self._create_event(
            SecurityEventType.AUTH_FAILURE,
            client_ip=client_ip,
            reason=self._redact(reason),
            user_id=self._redact(attempted_user),
            metadata=metadata or {},
        )
        self._logger.warning("Authentication failed", extra=event.to_dict())
        return event

    def log_authorization_denied(
        self,
        user_id: str,
        resource: str,
        action: str,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log authorization denial."""
        event = self._create_event(
            SecurityEventType.AUTHZ_DENIED,
            user_id=user_id,
            resource=resource,
            action=action,
            reason=reason,
            metadata=metadata or {},
        )
        self._logger.warning("Authorization denied", extra=event.to_dict())
        return event

    def log_rate_limit_exceeded(
        self,
        client_ip: str,
        endpoint: str,
        limit: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log rate limit exceeded event."""
        event = self._create_event(
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            client_ip=client_ip,
            resource=endpoint,
            reason=f"Rate limit exceeded: {limit}",
            user_id=user_id,
            metadata=metadata or {},
        )
        self._logger.warning("Rate limit exceeded", extra=event.to_dict())
        return event

    def log_secret_access(
        self,
        secret_name: str,
        accessor: str,
        action: str = "read",
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log secret access without exposing the secret value."""
        event = self._create_event(
            SecurityEventType.SECRET_ACCESS,
            resource=secret_name,
            user_id=accessor,
            action=action,
            metadata=metadata or {},
        )
        self._logger.info("Secret accessed", extra=event.to_dict())
        return event

    def log_token_revoked(
        self,
        user_id: str,
        token_jti: str,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log token revocation."""
        event = self._create_event(
            SecurityEventType.TOKEN_REVOKED,
            user_id=user_id,
            resource=token_jti,
            reason=reason,
            metadata=metadata or {},
        )
        self._logger.info("Token revoked", extra=event.to_dict())
        return event

    def log_suspicious_activity(
        self,
        client_ip: str,
        description: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log suspicious activity detection."""
        event = self._create_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            client_ip=client_ip,
            reason=self._redact(description),
            user_id=user_id,
            metadata=metadata or {},
        )
        self._logger.error("Suspicious activity detected", extra=event.to_dict())
        return event

    def log_privilege_escalation(
        self,
        user_id: str,
        from_role: str,
        to_role: str,
        client_ip: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log privilege escalation attempt (CRITICAL severity)."""
        event = self._create_event(
            SecurityEventType.PRIVILEGE_ESCALATION,
            severity=SecuritySeverity.CRITICAL,
            user_id=user_id,
            client_ip=client_ip,
            reason=f"Attempted escalation from '{from_role}' to '{to_role}'",
            metadata={"from_role": from_role, "to_role": to_role, **(metadata or {})},
        )
        self._logger.critical("Privilege escalation attempt", extra=event.to_dict())
        return event

    def log_data_export(
        self,
        user_id: str,
        resource: str,
        record_count: int,
        export_format: str,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log data export for compliance tracking."""
        event = self._create_event(
            SecurityEventType.DATA_EXPORT,
            user_id=user_id,
            resource=resource,
            action="export",
            metadata={
                "record_count": record_count,
                "format": export_format,
                **(metadata or {}),
            },
        )
        self._logger.info("Data exported", extra=event.to_dict())
        return event

    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: str | None = None,
        new_value: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log configuration change for audit trail."""
        # Redact sensitive values
        safe_old = "[REDACTED]" if old_value and "secret" in config_key.lower() else old_value
        safe_new = "[REDACTED]" if new_value and "secret" in config_key.lower() else new_value

        event = self._create_event(
            SecurityEventType.CONFIG_CHANGE,
            user_id=user_id,
            resource=config_key,
            action="update",
            metadata={
                "old_value": safe_old,
                "new_value": safe_new,
                **(metadata or {}),
            },
        )
        self._logger.warning("Configuration changed", extra=event.to_dict())
        return event

    def log_mfa_failure(
        self,
        user_id: str,
        client_ip: str,
        mfa_method: str,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log MFA verification failure (HIGH severity)."""
        event = self._create_event(
            SecurityEventType.MFA_FAILURE,
            user_id=user_id,
            client_ip=client_ip,
            action=mfa_method,
            reason="MFA verification failed",
            metadata=metadata or {},
        )
        self._logger.warning("MFA verification failed", extra=event.to_dict())
        return event


# Module-level singleton with thread-safe initialization
_audit_logger: SecurityAuditLogger | None = None
_audit_lock = threading.Lock()


def get_audit_logger() -> SecurityAuditLogger:
    """Get the global security audit logger instance (thread-safe)."""
    global _audit_logger
    if _audit_logger is None:
        with _audit_lock:
            if _audit_logger is None:
                _audit_logger = SecurityAuditLogger()
    return _audit_logger
