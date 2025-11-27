"""Authentication routes for login, logout, and token refresh.

**Feature: api-base-improvements**
**Validates: Requirements 1.1, 1.2, 1.4, 1.5**
"""

import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from my_api.core.auth.jwt import (
    JWTService,
    TokenExpiredError,
    TokenInvalidError,
    TokenPair,
    TokenPayload,
)
from my_api.core.auth.rbac import RBACUser
from my_api.core.config import get_settings
from my_api.infrastructure.auth.token_store import InMemoryTokenStore, RefreshTokenStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Module-level instances (will be replaced by DI in production)
_jwt_service: JWTService | None = None
_token_store: RefreshTokenStore | None = None


def get_jwt_service() -> JWTService:
    """Get JWT service instance."""
    global _jwt_service
    if _jwt_service is None:
        settings = get_settings()
        _jwt_service = JWTService(
            secret_key=settings.security.secret_key.get_secret_value(),
            algorithm=settings.security.algorithm,
            access_token_expire_minutes=settings.security.access_token_expire_minutes,
        )
    return _jwt_service


def get_token_store() -> RefreshTokenStore:
    """Get token store instance.

    Uses Redis if enabled in configuration, otherwise falls back to in-memory.
    """
    global _token_store
    if _token_store is None:
        # For sync context, use in-memory store
        # Redis store should be initialized at app startup
        _token_store = InMemoryTokenStore()
    return _token_store


def set_token_store(store: RefreshTokenStore) -> None:
    """Set the token store instance (for dependency injection).

    Args:
        store: Token store instance to use.
    """
    global _token_store
    _token_store = store


# Request/Response models
class TokenResponse(BaseModel):
    """Token pair response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str = Field(..., description="Refresh token to exchange")


class UserResponse(BaseModel):
    """Current user response."""

    id: str = Field(..., description="User ID")
    roles: list[str] = Field(default_factory=list, description="User roles")
    scopes: list[str] = Field(default_factory=list, description="Token scopes")


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# Demo user store (replace with real user service in production)
DEMO_USERS = {
    "admin": {"password": "admin123", "roles": ["admin"]},
    "user": {"password": "user123", "roles": ["user"]},
    "viewer": {"password": "viewer123", "roles": ["viewer"]},
}


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> RBACUser:
    """Get current authenticated user from token.

    Args:
        token: JWT access token from Authorization header.
        jwt_service: JWT service instance.

    Returns:
        RBACUser with user info from token.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    try:
        payload = jwt_service.verify_token(token, expected_type="access")
        return RBACUser(
            id=payload.sub,
            roles=list(payload.scopes),  # Using scopes as roles for simplicity
            scopes=list(payload.scopes),
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with credentials",
    description="Authenticate with username and password to receive access and refresh tokens.",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    token_store: Annotated[RefreshTokenStore, Depends(get_token_store)],
) -> TokenResponse:
    """Login endpoint.

    Args:
        form_data: OAuth2 password form with username and password.
        request: FastAPI request object.
        jwt_service: JWT service instance.
        token_store: Token store instance.

    Returns:
        TokenResponse with access and refresh tokens.

    Raises:
        HTTPException: If credentials are invalid.
    """
    # Demo authentication (replace with real user service)
    user = DEMO_USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token pair
    pair, _, refresh_payload = jwt_service.create_token_pair(
        user_id=form_data.username,
        scopes=user["roles"],
    )

    # Store refresh token
    await token_store.store(
        jti=refresh_payload.jti,
        user_id=form_data.username,
        expires_at=refresh_payload.exp,
    )

    logger.info(f"User logged in: {form_data.username}")

    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
        expires_in=pair.expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token.",
)
async def refresh_token(
    body: RefreshRequest,
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    token_store: Annotated[RefreshTokenStore, Depends(get_token_store)],
) -> TokenResponse:
    """Refresh token endpoint.

    Args:
        body: Request body with refresh token.
        jwt_service: JWT service instance.
        token_store: Token store instance.

    Returns:
        TokenResponse with new access and refresh tokens.

    Raises:
        HTTPException: If refresh token is invalid or revoked.
    """
    try:
        # Verify refresh token
        payload = jwt_service.verify_token(body.refresh_token, expected_type="refresh")

        # Check if token is still valid in store
        if not await token_store.is_valid(payload.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Revoke old refresh token
        await token_store.revoke(payload.jti)

        # Get user roles (in production, fetch from user service)
        user = DEMO_USERS.get(payload.sub, {"roles": []})

        # Create new token pair
        pair, _, new_refresh_payload = jwt_service.create_token_pair(
            user_id=payload.sub,
            scopes=user["roles"],
        )

        # Store new refresh token
        await token_store.store(
            jti=new_refresh_payload.jti,
            user_id=payload.sub,
            expires_at=new_refresh_payload.exp,
        )

        logger.info(f"Token refreshed for user: {payload.sub}")

        return TokenResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            token_type=pair.token_type,
            expires_in=pair.expires_in,
        )

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Invalidate the refresh token to logout the user.",
)
async def logout(
    body: RefreshRequest,
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    token_store: Annotated[RefreshTokenStore, Depends(get_token_store)],
) -> MessageResponse:
    """Logout endpoint.

    Args:
        body: Request body with refresh token.
        jwt_service: JWT service instance.
        token_store: Token store instance.

    Returns:
        MessageResponse confirming logout.
    """
    try:
        payload = jwt_service.verify_token(body.refresh_token, expected_type="refresh")
        await token_store.revoke(payload.jti)
        logger.info(f"User logged out: {payload.sub}")
    except (TokenExpiredError, TokenInvalidError):
        # Token already invalid, consider logout successful
        pass

    return MessageResponse(message="Successfully logged out")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
)
async def get_me(
    current_user: Annotated[RBACUser, Depends(get_current_user)],
) -> UserResponse:
    """Get current user endpoint.

    Args:
        current_user: Current authenticated user.

    Returns:
        UserResponse with user information.
    """
    return UserResponse(
        id=current_user.id,
        roles=current_user.roles,
        scopes=current_user.scopes,
    )


class RevokeTokenRequest(BaseModel):
    """Request to revoke a specific token."""

    token: str = Field(..., description="Token (access or refresh) to revoke")


class RevokeAllResponse(BaseModel):
    """Response for revoke all tokens operation."""

    message: str
    revoked_count: int = Field(..., description="Number of tokens revoked")


@router.post(
    "/revoke",
    response_model=MessageResponse,
    summary="Revoke a token",
    description="Revoke a specific access or refresh token.",
)
async def revoke_token(
    body: RevokeTokenRequest,
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    token_store: Annotated[RefreshTokenStore, Depends(get_token_store)],
) -> MessageResponse:
    """Revoke a specific token.

    **Feature: api-architecture-review**
    **Validates: Requirements 2.10**

    Args:
        body: Request body with token to revoke.
        jwt_service: JWT service instance.
        token_store: Token store instance.

    Returns:
        MessageResponse confirming revocation.
    """
    try:
        # Decode token to get JTI (without verifying expiration)
        payload = jwt_service.decode_token_unverified(body.token)
        revoked = await token_store.revoke(payload.jti)

        if revoked:
            logger.info(f"Token revoked: {payload.jti} for user {payload.sub}")
            return MessageResponse(message="Token successfully revoked")
        else:
            return MessageResponse(message="Token not found or already revoked")

    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token format",
        )


@router.post(
    "/revoke-all",
    response_model=RevokeAllResponse,
    summary="Revoke all tokens for current user",
    description="Revoke all refresh tokens for the authenticated user (logout from all devices).",
)
async def revoke_all_tokens(
    current_user: Annotated[RBACUser, Depends(get_current_user)],
    token_store: Annotated[RefreshTokenStore, Depends(get_token_store)],
) -> RevokeAllResponse:
    """Revoke all tokens for the current user.

    **Feature: api-architecture-review**
    **Validates: Requirements 2.10**

    Args:
        current_user: Current authenticated user.
        token_store: Token store instance.

    Returns:
        RevokeAllResponse with count of revoked tokens.
    """
    count = await token_store.revoke_all_for_user(current_user.id)
    logger.info(f"Revoked {count} tokens for user {current_user.id}")

    return RevokeAllResponse(
        message=f"Successfully revoked {count} tokens",
        revoked_count=count,
    )
