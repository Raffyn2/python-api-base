"""JWT authentication service for token generation and verification.

**Feature: core-code-review, api-best-practices-review-2025**
**Validates: Requirements 4.1, 4.4, 4.5, 11.1, 20.1, 20.2, 20.3**

**Feature: full-codebase-review-2025, Task 1.3: Refactored for file size compliance**
"""

from infrastructure.auth.jwt.errors import (
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
)
from infrastructure.auth.jwt.jwks import (
    JWKSService,
    get_jwks_service,
    initialize_jwks_service,
)
from infrastructure.auth.jwt.jwks_models import (
    JWK,
    JWKSResponse,
    KeyEntry,
    create_jwk_from_ec_public_key,
    create_jwk_from_rsa_public_key,
    generate_kid_from_public_key,
)
from infrastructure.auth.jwt.models import TokenPair, TokenPayload
from infrastructure.auth.jwt.protocols import KidNotFoundError
from infrastructure.auth.jwt.providers import (
    ES256Provider,
    HS256Provider,
    RS256Provider,
)
from infrastructure.auth.jwt.service import JWTService
from infrastructure.auth.jwt.time_source import SystemTimeSource, TimeSource

__all__ = [
    # JWKS Models
    "JWK",
    "ES256Provider",
    "HS256Provider",
    "JWKSResponse",
    # JWKS Service
    "JWKSService",
    # Service
    "JWTService",
    "KeyEntry",
    "KidNotFoundError",
    # Providers
    "RS256Provider",
    # Time
    "SystemTimeSource",
    "TimeSource",
    # Errors
    "TokenExpiredError",
    "TokenInvalidError",
    # Models
    "TokenPair",
    "TokenPayload",
    "TokenRevokedError",
    "create_jwk_from_ec_public_key",
    "create_jwk_from_rsa_public_key",
    "generate_kid_from_public_key",
    "get_jwks_service",
    "initialize_jwks_service",
]
