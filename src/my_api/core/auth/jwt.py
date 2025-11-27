"""JWT authentication service for token generation and verification.

**Feature: api-base-improvements**
**Validates: Requirements 1.1, 1.2, 1.3, 1.6**
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from my_api.core.exceptions import AuthenticationError
from my_api.shared.utils.ids import generate_ulid


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""

    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(message=message)
        self.error_code = "TOKEN_EXPIRED"


class TokenInvalidError(AuthenticationError):
    """Raised when a token is invalid or malformed."""

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message=message)
        self.error_code = "TOKEN_INVALID"


class TokenRevokedError(AuthenticationError):
    """Raised when a token has been revoked."""

    def __init__(self, message: str = "Token has been revoked") -> None:
        super().__init__(message=message)
        self.error_code = "TOKEN_REVOKED"


@dataclass(frozen=True)
class TokenPayload:
    """JWT token payload data.

    Attributes:
        sub: Subject (user_id).
        exp: Expiration timestamp.
        iat: Issued at timestamp.
        jti: JWT ID for revocation tracking.
        scopes: List of permission scopes.
        token_type: Type of token (access or refresh).
    """

    sub: str
    exp: datetime
    iat: datetime
    jti: str
    scopes: tuple[str, ...] = field(default_factory=tuple)
    token_type: str = "access"

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary for JWT encoding.

        Returns:
            Dictionary representation of the payload.
        """
        return {
            "sub": self.sub,
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
            "jti": self.jti,
            "scopes": list(self.scopes),
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenPayload":
        """Create TokenPayload from dictionary.

        Args:
            data: Dictionary with payload data.

        Returns:
            TokenPayload instance.
        """
        return cls(
            sub=data["sub"],
            exp=datetime.fromtimestamp(data["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(data["iat"], tz=timezone.utc),
            jti=data["jti"],
            scopes=tuple(data.get("scopes", [])),
            token_type=data.get("token_type", "access"),
        )

    def pretty_print(self) -> str:
        """Format token payload for debugging.

        Returns:
            Formatted string representation.
        """
        lines = [
            "TokenPayload {",
            f"  sub: {self.sub}",
            f"  exp: {self.exp.isoformat()}",
            f"  iat: {self.iat.isoformat()}",
            f"  jti: {self.jti}",
            f"  scopes: {list(self.scopes)}",
            f"  token_type: {self.token_type}",
            "}",
        ]
        return "\n".join(lines)


@dataclass(frozen=True)
class TokenPair:
    """Access and refresh token pair.

    Attributes:
        access_token: JWT access token string.
        refresh_token: JWT refresh token string.
        token_type: Token type for Authorization header.
        expires_in: Access token expiration in seconds.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response.

        Returns:
            Dictionary representation.
        """
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }


class JWTService:
    """Service for JWT token operations.

    Handles creation, verification, and refresh of JWT tokens
    using the python-jose library.
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ) -> None:
        """Initialize JWT service.

        Args:
            secret_key: Secret key for signing tokens.
            algorithm: JWT signing algorithm.
            access_token_expire_minutes: Access token TTL in minutes.
            refresh_token_expire_days: Refresh token TTL in days.
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expire = timedelta(minutes=access_token_expire_minutes)
        self._refresh_expire = timedelta(days=refresh_token_expire_days)

    def create_access_token(
        self,
        user_id: str,
        scopes: list[str] | None = None,
    ) -> tuple[str, TokenPayload]:
        """Create a new access token.

        Args:
            user_id: User identifier to encode in token.
            scopes: Optional list of permission scopes.

        Returns:
            Tuple of (token_string, payload).
        """
        now = datetime.now(timezone.utc)
        payload = TokenPayload(
            sub=user_id,
            exp=now + self._access_expire,
            iat=now,
            jti=generate_ulid(),
            scopes=tuple(scopes or []),
            token_type="access",
        )

        token = jwt.encode(
            payload.to_dict(),
            self._secret_key,
            algorithm=self._algorithm,
        )

        return token, payload

    def create_refresh_token(self, user_id: str) -> tuple[str, TokenPayload]:
        """Create a new refresh token.

        Args:
            user_id: User identifier to encode in token.

        Returns:
            Tuple of (token_string, payload).
        """
        now = datetime.now(timezone.utc)
        payload = TokenPayload(
            sub=user_id,
            exp=now + self._refresh_expire,
            iat=now,
            jti=generate_ulid(),
            scopes=(),
            token_type="refresh",
        )

        token = jwt.encode(
            payload.to_dict(),
            self._secret_key,
            algorithm=self._algorithm,
        )

        return token, payload

    def create_token_pair(
        self,
        user_id: str,
        scopes: list[str] | None = None,
    ) -> tuple[TokenPair, TokenPayload, TokenPayload]:
        """Create both access and refresh tokens.

        Args:
            user_id: User identifier.
            scopes: Optional permission scopes for access token.

        Returns:
            Tuple of (TokenPair, access_payload, refresh_payload).
        """
        access_token, access_payload = self.create_access_token(user_id, scopes)
        refresh_token, refresh_payload = self.create_refresh_token(user_id)

        pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(self._access_expire.total_seconds()),
        )

        return pair, access_payload, refresh_payload

    def verify_token(
        self,
        token: str,
        expected_type: str | None = None,
    ) -> TokenPayload:
        """Verify and decode a JWT token.

        Args:
            token: JWT token string to verify.
            expected_type: Expected token type (access/refresh).

        Returns:
            Decoded TokenPayload.

        Raises:
            TokenExpiredError: If token has expired.
            TokenInvalidError: If token is invalid or malformed.
        """
        try:
            data = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except JWTError as e:
            error_msg = str(e).lower()
            if "expired" in error_msg:
                raise TokenExpiredError() from e
            raise TokenInvalidError(f"Token verification failed: {e}") from e

        payload = TokenPayload.from_dict(data)

        # Check expiration explicitly
        if payload.exp < datetime.now(timezone.utc):
            raise TokenExpiredError()

        # Validate token type if specified
        if expected_type and payload.token_type != expected_type:
            raise TokenInvalidError(
                f"Expected {expected_type} token, got {payload.token_type}"
            )

        return payload

    def decode_token_unverified(self, token: str) -> TokenPayload:
        """Decode token without verification (for debugging).

        Args:
            token: JWT token string.

        Returns:
            Decoded TokenPayload.

        Raises:
            TokenInvalidError: If token cannot be decoded.
        """
        try:
            data = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"verify_exp": False},
            )
            return TokenPayload.from_dict(data)
        except JWTError as e:
            raise TokenInvalidError(f"Cannot decode token: {e}") from e
