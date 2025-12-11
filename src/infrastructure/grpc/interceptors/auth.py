"""JWT authentication interceptor for gRPC.

This module provides an interceptor that validates JWT tokens
from gRPC metadata for authentication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from grpc import StatusCode, aio
from structlog import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

logger = get_logger(__name__)

AUTHORIZATION_HEADER = "authorization"
BEARER_PREFIX = "bearer "


class AuthInterceptor(aio.ServerInterceptor):
    """JWT authentication interceptor.

    Validates JWT tokens from the authorization metadata header.
    """

    def __init__(
        self,
        jwt_validator: Callable[[str], dict[str, Any] | None],
        excluded_methods: set[str] | None = None,
    ) -> None:
        """Initialize auth interceptor.

        Args:
            jwt_validator: Function to validate JWT and return claims
            excluded_methods: Set of method names to exclude from auth
        """
        self._jwt_validator = jwt_validator
        self._excluded_methods = excluded_methods or {
            "/grpc.health.v1.Health/Check",
            "/grpc.health.v1.Health/Watch",
            "/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo",
        }

    async def intercept_service(
        self,
        continuation: Callable[..., Any],
        handler_call_details: aio.HandlerCallDetails,
    ) -> aio.RpcMethodHandler:
        """Intercept and validate JWT token from metadata.

        Args:
            continuation: The next handler in chain
            handler_call_details: Details about the RPC call

        Returns:
            The RPC method handler
        """
        method = handler_call_details.method

        # Skip auth for excluded methods
        if method in self._excluded_methods:
            return await continuation(handler_call_details)

        # Extract token from metadata
        metadata = dict(handler_call_details.invocation_metadata or [])
        auth_header = metadata.get(AUTHORIZATION_HEADER, "")

        if not auth_header.lower().startswith(BEARER_PREFIX):
            logger.warning(
                "grpc_auth_missing_token",
                method=method,
            )
            return self._create_abort_handler(
                StatusCode.UNAUTHENTICATED,
                "Missing or invalid authorization header",
            )

        token = auth_header[len(BEARER_PREFIX) :]

        try:
            claims = self._jwt_validator(token)
            if claims is None:
                logger.warning(
                    "grpc_auth_invalid_token",
                    method=method,
                )
                return self._create_abort_handler(
                    StatusCode.UNAUTHENTICATED,
                    "Invalid token",
                )

            logger.info(
                "grpc_auth_success",
                method=method,
                user_id=claims.get("sub"),
            )

            # Continue with the request
            return await continuation(handler_call_details)

        except Exception:
            logger.exception(
                "grpc_auth_error",
                method=method,
            )
            return self._create_abort_handler(
                StatusCode.UNAUTHENTICATED,
                "Authentication failed",
            )

    def _create_abort_handler(
        self,
        code: StatusCode,
        details: str,
    ) -> aio.RpcMethodHandler:
        """Create a handler that aborts with the given status.

        Args:
            code: The gRPC status code
            details: Error details message

        Returns:
            An RPC method handler that aborts
        """

        async def abort_handler(
            request: Any,
            context: aio.ServicerContext,
        ) -> None:
            await context.abort(code, details)

        return aio.unary_unary_rpc_method_handler(abort_handler)


def create_jwt_validator(
    secret_key: str,
    algorithm: str = "HS256",
) -> Callable[[str], dict[str, Any] | None]:
    """Create a JWT validator function.

    Args:
        secret_key: The secret key for JWT validation
        algorithm: The JWT algorithm

    Returns:
        A validator function
    """
    try:
        from jose import JWTError, jwt

        def validate(token: str) -> dict[str, Any] | None:
            try:
                return jwt.decode(token, secret_key, algorithms=[algorithm])
            except JWTError:
                return None

        return validate
    except ImportError:
        logger.warning("python-jose not installed, JWT validation disabled")
        return lambda _: None
