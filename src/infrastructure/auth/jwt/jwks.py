"""JWKS (JSON Web Key Set) service for key distribution.

**Feature: api-best-practices-review-2025**
**Validates: Requirements 2.1, 20.1, 20.2, 20.3, 20.4, 20.6**

Implements:
- JWKS endpoint generation for RS256/ES256 public keys
- Key ID (kid) generation and validation
- Key rotation support with grace period
- Algorithm enforcement
"""

import base64
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class JWK:
    """JSON Web Key representation.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 20.2**
    """

    kty: str  # Key type (RSA, EC)
    kid: str  # Key ID
    use: str  # Key use (sig)
    alg: str  # Algorithm (RS256, ES256)
    n: str | None = None  # RSA modulus (base64url)
    e: str | None = None  # RSA exponent (base64url)
    crv: str | None = None  # EC curve (P-256)
    x: str | None = None  # EC x coordinate (base64url)
    y: str | None = None  # EC y coordinate (base64url)

    def to_dict(self) -> dict[str, Any]:
        """Convert JWK to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "kty": self.kty,
            "kid": self.kid,
            "use": self.use,
            "alg": self.alg,
        }
        if self.kty == "RSA":
            result["n"] = self.n
            result["e"] = self.e
        elif self.kty == "EC":
            result["crv"] = self.crv
            result["x"] = self.x
            result["y"] = self.y
        return result


@dataclass(frozen=True, slots=True)
class JWKSResponse:
    """JWKS response containing multiple keys.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 20.2, 20.3**
    """

    keys: tuple[JWK, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert JWKS to dictionary for JSON response."""
        return {"keys": [key.to_dict() for key in self.keys]}


@dataclass
class KeyEntry:
    """Internal key entry with metadata for rotation."""

    kid: str
    public_key_pem: str
    algorithm: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    revoked_at: datetime | None = None
    expires_at: datetime | None = None


def _base64url_encode(data: bytes) -> str:
    """Encode bytes to base64url without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _int_to_base64url(num: int) -> str:
    """Convert integer to base64url encoding."""
    byte_length = (num.bit_length() + 7) // 8
    return _base64url_encode(num.to_bytes(byte_length, byteorder="big"))


def generate_kid_from_public_key(public_key_pem: str) -> str:
    """Generate a deterministic key ID from public key.

    Uses SHA-256 hash of the public key DER encoding, truncated to 16 chars.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 20.1**

    Args:
        public_key_pem: Public key in PEM format.

    Returns:
        Key ID string (16 hex characters).
    """
    # Hash the PEM content for deterministic kid
    key_hash = hashlib.sha256(public_key_pem.encode()).digest()
    return key_hash[:8].hex()


def create_jwk_from_rsa_public_key(public_key_pem: str, kid: str) -> JWK:
    """Create JWK from RSA public key PEM.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 20.2**

    Args:
        public_key_pem: RSA public key in PEM format.
        kid: Key ID to use.

    Returns:
        JWK representation of the public key.
    """
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    # Load and parse the public key
    public_key = load_pem_public_key(public_key_pem.encode())

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Expected RSA public key")

    numbers = public_key.public_numbers()

    return JWK(
        kty="RSA",
        kid=kid,
        use="sig",
        alg="RS256",
        n=_int_to_base64url(numbers.n),
        e=_int_to_base64url(numbers.e),
    )


def create_jwk_from_ec_public_key(public_key_pem: str, kid: str) -> JWK:
    """Create JWK from EC public key PEM.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 20.2**

    Args:
        public_key_pem: EC public key in PEM format.
        kid: Key ID to use.

    Returns:
        JWK representation of the public key.
    """
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    public_key = load_pem_public_key(public_key_pem.encode())

    if not isinstance(public_key, ec.EllipticCurvePublicKey):
        raise ValueError("Expected EC public key")

    numbers = public_key.public_numbers()

    # P-256 uses 32 byte coordinates
    x_bytes = numbers.x.to_bytes(32, byteorder="big")
    y_bytes = numbers.y.to_bytes(32, byteorder="big")

    return JWK(
        kty="EC",
        kid=kid,
        use="sig",
        alg="ES256",
        crv="P-256",
        x=_base64url_encode(x_bytes),
        y=_base64url_encode(y_bytes),
    )


def extract_public_key_from_private(private_key_pem: str) -> str:
    """Extract public key PEM from private key PEM.

    Args:
        private_key_pem: Private key in PEM format.

    Returns:
        Public key in PEM format.
    """
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PublicFormat,
        load_pem_private_key,
    )

    private_key = load_pem_private_key(private_key_pem.encode(), password=None)
    public_key = private_key.public_key()

    return public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    ).decode()


class JWKSService:
    """Service for managing JWKS and key rotation.

    **Feature: api-best-practices-review-2025**
    **Validates: Requirements 20.2, 20.3, 20.4, 20.6**

    Supports:
    - Multiple active keys for rotation
    - Grace period for old keys
    - Key revocation
    - Algorithm-specific JWK generation

    Example:
        >>> service = JWKSService()
        >>> service.add_key(public_key_pem, "RS256")
        >>> jwks = service.get_jwks()
        >>> # Expose at /.well-known/jwks.json
    """

    def __init__(
        self,
        grace_period: timedelta = timedelta(hours=24),
        max_keys: int = 5,
    ) -> None:
        """Initialize JWKS service.

        Args:
            grace_period: How long to keep old keys after rotation.
            max_keys: Maximum number of keys to keep in the set.
        """
        self._keys: list[KeyEntry] = []
        self._grace_period = grace_period
        self._max_keys = max_keys
        self._current_kid: str | None = None

    def add_key(
        self,
        public_key_pem: str,
        algorithm: str,
        kid: str | None = None,
        make_current: bool = True,
    ) -> str:
        """Add a new key to the JWKS.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 20.3**

        Args:
            public_key_pem: Public key in PEM format.
            algorithm: Algorithm (RS256 or ES256).
            kid: Optional key ID (generated if not provided).
            make_current: Whether to make this the current signing key.

        Returns:
            Key ID of the added key.
        """
        if kid is None:
            kid = generate_kid_from_public_key(public_key_pem)

        entry = KeyEntry(
            kid=kid,
            public_key_pem=public_key_pem,
            algorithm=algorithm,
        )
        self._keys.append(entry)

        if make_current:
            self._current_kid = kid

        # Prune old keys beyond max
        self._cleanup_old_keys()

        logger.info(
            "Added key to JWKS",
            extra={"kid": kid, "algorithm": algorithm, "is_current": make_current},
        )

        return kid

    def add_key_from_private(
        self,
        private_key_pem: str,
        algorithm: str,
        kid: str | None = None,
        make_current: bool = True,
    ) -> str:
        """Add a key from private key (extracts public key).

        Args:
            private_key_pem: Private key in PEM format.
            algorithm: Algorithm (RS256 or ES256).
            kid: Optional key ID.
            make_current: Whether to make this the current signing key.

        Returns:
            Key ID of the added key.
        """
        public_key_pem = extract_public_key_from_private(private_key_pem)
        return self.add_key(public_key_pem, algorithm, kid, make_current)

    def revoke_key(self, kid: str) -> bool:
        """Revoke a key immediately.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 20.6**

        Args:
            kid: Key ID to revoke.

        Returns:
            True if key was found and revoked.
        """
        for entry in self._keys:
            if entry.kid == kid:
                # Create new entry with revocation time
                idx = self._keys.index(entry)
                self._keys[idx] = KeyEntry(
                    kid=entry.kid,
                    public_key_pem=entry.public_key_pem,
                    algorithm=entry.algorithm,
                    created_at=entry.created_at,
                    revoked_at=datetime.now(UTC),
                    expires_at=entry.expires_at,
                )
                logger.warning("Revoked key", extra={"kid": kid})
                return True
        return False

    def rotate_current_key(
        self,
        new_public_key_pem: str,
        algorithm: str,
        kid: str | None = None,
    ) -> str:
        """Rotate to a new current key with grace period.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 20.3**

        Args:
            new_public_key_pem: New public key in PEM format.
            algorithm: Algorithm for the new key.
            kid: Optional key ID for the new key.

        Returns:
            Key ID of the new current key.
        """
        # Mark old current key with expiration
        if self._current_kid:
            for i, entry in enumerate(self._keys):
                if entry.kid == self._current_kid:
                    self._keys[i] = KeyEntry(
                        kid=entry.kid,
                        public_key_pem=entry.public_key_pem,
                        algorithm=entry.algorithm,
                        created_at=entry.created_at,
                        revoked_at=entry.revoked_at,
                        expires_at=datetime.now(UTC) + self._grace_period,
                    )
                    break

        # Add new key as current
        return self.add_key(new_public_key_pem, algorithm, kid, make_current=True)

    def get_current_kid(self) -> str | None:
        """Get the current signing key ID."""
        return self._current_kid

    def get_key(self, kid: str) -> KeyEntry | None:
        """Get a key entry by ID.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 20.4**

        Args:
            kid: Key ID to look up.

        Returns:
            KeyEntry if found and not revoked, None otherwise.
        """
        for entry in self._keys:
            if entry.kid == kid and entry.revoked_at is None:
                return entry
        return None

    def validate_kid(self, kid: str) -> bool:
        """Validate that a kid exists in the JWKS.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 20.4**

        Args:
            kid: Key ID from token header.

        Returns:
            True if kid is valid and key is not revoked.
        """
        entry = self.get_key(kid)
        if entry is None:
            return False

        # Check if expired
        if entry.expires_at and entry.expires_at < datetime.now(UTC):
            return False

        return True

    def get_jwks(self) -> JWKSResponse:
        """Get the JWKS for the well-known endpoint.

        **Feature: api-best-practices-review-2025**
        **Validates: Requirements 20.2**

        Returns:
            JWKSResponse containing all active (non-revoked) keys.
        """
        self._cleanup_old_keys()

        jwks: list[JWK] = []
        now = datetime.now(UTC)

        for entry in self._keys:
            # Skip revoked keys
            if entry.revoked_at is not None:
                continue

            # Skip expired keys
            if entry.expires_at and entry.expires_at < now:
                continue

            try:
                if entry.algorithm == "RS256":
                    jwk = create_jwk_from_rsa_public_key(entry.public_key_pem, entry.kid)
                elif entry.algorithm == "ES256":
                    jwk = create_jwk_from_ec_public_key(entry.public_key_pem, entry.kid)
                else:
                    continue
                jwks.append(jwk)
            except Exception as e:
                logger.error(f"Failed to create JWK for kid={entry.kid}: {e}")

        return JWKSResponse(keys=tuple(jwks))

    def _cleanup_old_keys(self) -> None:
        """Remove expired and revoked keys beyond grace period."""
        now = datetime.now(UTC)

        # Remove keys that are past grace period after expiration or revocation
        self._keys = [
            entry
            for entry in self._keys
            if not self._should_remove_key(entry, now)
        ]

        # Keep only max_keys most recent
        if len(self._keys) > self._max_keys:
            # Sort by created_at descending, keep newest
            self._keys.sort(key=lambda e: e.created_at, reverse=True)
            self._keys = self._keys[: self._max_keys]

    def _should_remove_key(self, entry: KeyEntry, now: datetime) -> bool:
        """Check if a key should be removed."""
        # Revoked keys are removed after grace period
        if entry.revoked_at:
            return (now - entry.revoked_at) > self._grace_period

        # Expired keys are removed after grace period
        if entry.expires_at:
            return (now - entry.expires_at) > self._grace_period

        return False


# Global singleton for JWKS service
_jwks_service: JWKSService | None = None


def get_jwks_service() -> JWKSService:
    """Get the global JWKS service instance."""
    global _jwks_service
    if _jwks_service is None:
        _jwks_service = JWKSService()
    return _jwks_service


def initialize_jwks_service(
    private_key_pem: str | None = None,
    public_key_pem: str | None = None,
    algorithm: str = "RS256",
    grace_period: timedelta = timedelta(hours=24),
) -> JWKSService:
    """Initialize the global JWKS service with initial key.

    Args:
        private_key_pem: Optional private key to extract public key from.
        public_key_pem: Optional public key directly.
        algorithm: Algorithm for the key.
        grace_period: Grace period for key rotation.

    Returns:
        Initialized JWKSService.
    """
    global _jwks_service
    _jwks_service = JWKSService(grace_period=grace_period)

    if private_key_pem:
        _jwks_service.add_key_from_private(private_key_pem, algorithm)
    elif public_key_pem:
        _jwks_service.add_key(public_key_pem, algorithm)

    return _jwks_service
