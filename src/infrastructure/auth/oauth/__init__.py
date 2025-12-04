"""Generic OAuth providers with PEP 695 type parameters.

**Feature: enterprise-generics-2025**
**Requirement: R13 - Generic Authentication System**

Exports:
    - OAuthProvider[TUser, TClaims]: Generic OAuth provider protocol
    - KeycloakProvider[TUser, TClaims]: Keycloak implementation
    - Auth0Provider[TUser, TClaims]: Auth0 implementation
    - AuthResult[TUser, TClaims]: Authentication result
    - TokenPair[TClaims]: Access/refresh token pair
"""

from infrastructure.auth.oauth.auth0 import Auth0Config, Auth0Provider
from infrastructure.auth.oauth.keycloak import KeycloakConfig, KeycloakProvider
from infrastructure.auth.oauth.provider import (
    AuthError,
    AuthResult,
    OAuthConfig,
    OAuthProvider,
    TokenPair,
)

__all__ = [
    "Auth0Config",
    # Auth0
    "Auth0Provider",
    "AuthError",
    "AuthResult",
    "KeycloakConfig",
    # Keycloak
    "KeycloakProvider",
    "OAuthConfig",
    # Core
    "OAuthProvider",
    "TokenPair",
]
