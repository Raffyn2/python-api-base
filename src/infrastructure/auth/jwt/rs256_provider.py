"""RS256 JWT algorithm provider.

**Feature: api-base-score-100, api-best-practices-review-2025**
**Validates: Requirements 1.1, 1.2, 20.1, 20.2**
**Refactored: Split from providers.py for one-class-per-file compliance**
"""

from datetime import timedelta

from infrastructure.auth.jwt.exceptions import InvalidKeyError
from infrastructure.auth.jwt.jwks import (
    extract_public_key_from_private,
    generate_kid_from_public_key,
)
from infrastructure.auth.jwt.protocols import BaseJWTProvider


class RS256Provider(BaseJWTProvider):
    """RS256 (RSA + SHA-256) provider for asymmetric JWT.

    **Feature: api-base-score-100, api-best-practices-review-2025**
    **Validates: Requirements 1.1, 1.2, 20.1, 20.2**

    Uses RSA private key for signing and public key for verification.
    Recommended for production environments where key distribution is a concern.

    Security Features:
        - Asymmetric cryptography (public/private key pair)
        - RSA 2048-bit keys recommended
        - PEM format support
        - Prevents algorithm confusion attacks
        - Auto-generated kid for JWKS support

    Example:
        >>> provider = RS256Provider(
        ...     private_key=PRIVATE_KEY_PEM,
        ...     public_key=PUBLIC_KEY_PEM,
        ...     issuer="my-api",
        ...     audience="my-app",
        ... )
        >>> token = provider.sign({"sub": "user123", "roles": ["admin"]})
        >>> claims = provider.verify(token)
        >>> # Token header includes kid for JWKS lookup
    """

    def __init__(
        self,
        private_key: str | None = None,
        public_key: str | None = None,
        issuer: str | None = None,
        audience: str | None = None,
        default_expiry: timedelta = timedelta(hours=1),
        kid: str | None = None,
    ) -> None:
        """Initialize RS256 provider.

        Args:
            private_key: RSA private key in PEM format (required for signing).
            public_key: RSA public key in PEM format (required for verification).
            issuer: Token issuer claim (iss). Optional.
            audience: Token audience claim (aud). Optional.
            default_expiry: Default token expiration time. Default: 1 hour.
            kid: Key ID for JWKS. Auto-generated from public key if not provided.

        Raises:
            InvalidKeyError: If neither private nor public key provided,
                or if key format is invalid.
        """
        if not private_key and not public_key:
            raise InvalidKeyError(
                "RS256 requires at least one of private_key or public_key",
            )

        self._private_key = private_key
        self._public_key = public_key

        self._validate_keys()

        # Auto-generate kid from public key if not provided
        if kid is None:
            kid = self._generate_kid()

        super().__init__(issuer, audience, default_expiry, kid)

    def _generate_kid(self) -> str:
        """Generate key ID from public key.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 20.1**
        """
        if self._public_key:
            return generate_kid_from_public_key(self._public_key)
        if self._private_key:
            public_pem = extract_public_key_from_private(self._private_key)
            return generate_kid_from_public_key(public_pem)
        return ""

    def _validate_keys(self) -> None:
        """Validate RSA key format.

        Raises:
            InvalidKeyError: If key format is invalid.
        """
        if self._private_key and "-----BEGIN" not in self._private_key:
            raise InvalidKeyError(
                "Invalid RSA private key format. Expected PEM format (must start with -----BEGIN).",
            )
        if self._public_key and "-----BEGIN" not in self._public_key:
            raise InvalidKeyError(
                "Invalid RSA public key format. Expected PEM format (must start with -----BEGIN).",
            )

    @property
    def algorithm(self) -> str:
        """Get the algorithm name."""
        return "RS256"

    def _get_signing_key(self) -> str:
        """Get RSA private key for signing.

        Returns:
            RSA private key in PEM format.

        Raises:
            InvalidKeyError: If private key not provided.
        """
        if not self._private_key:
            raise InvalidKeyError("Private key required for signing")
        return self._private_key

    def _get_verification_key(self) -> str:
        """Get RSA public key for verification.

        Returns:
            RSA public key in PEM format. Falls back to private key if public key
            is not provided (jose library can extract public key from private key).

        Raises:
            InvalidKeyError: If neither public nor private key provided.
        """
        if self._public_key:
            return self._public_key
        if self._private_key:
            # jose library can extract public key from private key
            return self._private_key
        raise InvalidKeyError("Public key required for verification")
