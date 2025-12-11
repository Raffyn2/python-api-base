import logging
from unittest.mock import Mock

import pytest

from infrastructure.security.audit_logger.enums import SecurityEventType
from infrastructure.security.audit_logger.service import (
    SecurityAuditLogger,
    get_audit_logger,
)


@pytest.fixture()
def mock_logger() -> Mock:
    return Mock(spec=logging.Logger)


@pytest.fixture()
def audit_logger(mock_logger: Mock) -> SecurityAuditLogger:
    return SecurityAuditLogger(logger=mock_logger)


class TestSecurityAuditLogger:
    def test_redact_pii(self) -> None:
        logger = SecurityAuditLogger(redact_pii=True)
        assert logger._redact("test@example.com") == "[EMAIL]"
        assert logger._redact("no pii") == "no pii"

    def test_redact_ip(self) -> None:
        logger = SecurityAuditLogger(redact_ip_addresses=True)
        assert logger._redact("127.0.0.1") == "[IP_REDACTED]"

    def test_log_auth_success(self, audit_logger: SecurityAuditLogger, mock_logger: Mock) -> None:
        event = audit_logger.log_auth_success(user_id="test_user", client_ip="1.2.3.4", method="password")
        assert event.event_type == SecurityEventType.AUTH_SUCCESS
        mock_logger.info.assert_called_once()

    def test_log_auth_failure(self, audit_logger: SecurityAuditLogger, mock_logger: Mock) -> None:
        event = audit_logger.log_auth_failure(client_ip="1.2.3.4", reason="bad password", attempted_user="test_user")
        assert event.event_type == SecurityEventType.AUTH_FAILURE
        mock_logger.warning.assert_called_once()

    def test_log_authorization_denied(self, audit_logger: SecurityAuditLogger, mock_logger: Mock) -> None:
        event = audit_logger.log_authorization_denied(user_id="test_user", resource="test_resource", action="read")
        assert event.event_type == SecurityEventType.AUTHZ_DENIED
        mock_logger.warning.assert_called_once()

    def test_log_rate_limit_exceeded(self, audit_logger: SecurityAuditLogger, mock_logger: Mock) -> None:
        event = audit_logger.log_rate_limit_exceeded(client_ip="1.2.3.4", endpoint="/test", limit="10/min")
        assert event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
        mock_logger.warning.assert_called_once()

    def test_log_secret_access(self, audit_logger: SecurityAuditLogger, mock_logger: Mock) -> None:
        event = audit_logger.log_secret_access(secret_name="test_secret", accessor="test_user")
        assert event.event_type == SecurityEventType.SECRET_ACCESS
        mock_logger.info.assert_called_once()

    def test_log_token_revoked(self, audit_logger: SecurityAuditLogger, mock_logger: Mock) -> None:
        event = audit_logger.log_token_revoked(user_id="test_user", token_jti="test_jti")
        assert event.event_type == SecurityEventType.TOKEN_REVOKED
        mock_logger.info.assert_called_once()

    def test_log_suspicious_activity(self, audit_logger: SecurityAuditLogger, mock_logger: Mock) -> None:
        event = audit_logger.log_suspicious_activity(client_ip="1.2.3.4", description="test activity")
        assert event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
        mock_logger.error.assert_called_once()


def test_get_audit_logger() -> None:
    logger1 = get_audit_logger()
    logger2 = get_audit_logger()
    assert logger1 is logger2
