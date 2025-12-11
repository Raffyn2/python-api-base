"""HS256 JWT algorithm provider.

**Feature: api-base-score-100**
**Validates: Requirements 1.4**
**Refactored: Split from providers.py for one-class-per-file compliance**
"""

from datetime import timedelta

import structlog

from infrastructure.auth.jwt.exceptions import InvalidKeyError
from infrastructure.auth.jwt.protocols import BaseJWTProvider

logger = structlog.get_logger(__name__)


class HS256Provider(BaseJWTProvider):
    """HS256 (HMAC + SHA-256) provider for symmetric JWT.

    **Feature: api-base-score-100, Task 1.1: Add RS256/ES256 provider classes**
    **Validates: Requirements 1.4**

    Uses shared secret for both signing and verification.

    **SECURITY WARNING**:
        - NOT recommended for production environments
        - Symmetric algorithm means same key for signing and verification
        - Anyone with the key can both create and verify tokens
        - Use RS256 or ES256 instead for production
        - Only use HS256 for development/testing

    Example:
        >>> # Development only - NOT for production!
        >>> provider = HS256Provider(
        ...     secret_key="dev-secret-key-minimum-32-chars",
        ...     production_mode=False,  # Will warn if True
        ... )
        >>> token = provider.sign({"sub": "user123"})
        >>> claims = provider.verify(token)
    """

    def __init__(
        self,
        secret_key: str,
        issuer: str | None = None,
        audience: str | None = None,
        default_expiry: timedelta = timedelta(hours=1),
        production_mode: bool = False,
    ) -> None:
        """Initialize HS256 provider.

        Args:
            secret_key: Shared secret for signing/verification (min 32 chars).
            issuer: Token issuer claim (iss). Optional.
            audience: Token audience claim (aud). Optional.
            default_expiry: Default token expiration time. Default: 1 hour.
            production_mode: If True, logs security warning about HS256 usage.

        Raises:
            InvalidKeyError: If secret_key is empty or too short.
        """
        super().__init__(issuer, audience, default_expiry)

        if not secret_key or len(secret_key) < 32:
            raise InvalidKeyError(
                "HS256 secret_key must be at least 32 characters for security",
            )

        self._secret_key = secret_key

        if production_mode:
            logger.warning(
                "SECURITY WARNING: HS256 algorithm used in production mode. "
                "HS256 is a symmetric algorithm and NOT recommended for production. "
                "Consider using RS256 or ES256 for enhanced security.",
                algorithm="HS256",
                operation="INIT",
                security_level="LOW",
            )

    @property
    def algorithm(self) -> str:
        """Get the algorithm name."""
        return "HS256"

    def _get_signing_key(self) -> str:
        """Get secret key for signing.

        Returns:
            Shared secret key.
        """
        return self._secret_key

    def _get_verification_key(self) -> str:
        """Get secret key for verification.

        Returns:
            Shared secret key (same as signing key).
        """
        return self._secret_key
