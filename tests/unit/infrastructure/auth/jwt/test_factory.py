"""Unit tests for JWT provider factory.

Tests create_jwt_provider function with different algorithms.
"""

import pytest

from infrastructure.auth.jwt.config import JWTKeyConfig
from infrastructure.auth.jwt.exceptions import InvalidKeyError
from infrastructure.auth.jwt.factory import create_jwt_provider
from infrastructure.auth.jwt.providers import (
    ES256Provider,
    HS256Provider,
    RS256Provider,
)

# Test keys for unit tests only - NOT for production
TEST_RSA_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7MmM2rMHRqWdSpYfE
8pHgMPLGHvmDpvv8zBVAqEV7hXB4R7RLBK6P1yVkBP9fU7Q8YXH4cPpOsQF8xkQx
N5rinGKwjEBsXhsLfwBKNL0HOuTJRUBiTlZsXqoAL1krWjPYFClGQzwqFzp9Qf1D
5NWFVi/og/V8DXU7E/DN7E7ADL8pI7VxwcL/FPFhMA8LhwPp0sanY8bRjPUMlYOZ
M7sFFzGMwKvCjNE8GZKBwMgmLvlbms7gmBkXPh8jFSwMi0s+DSjI0fvCJkGYpOSi
ND1otALUouObF/Z7eeU7MHywdXFqxXcYBniitQIDAQABAoIBAFJ+nyHGSigXSjkr
E+MBmm/U0LwoxnPtkfPvSSYpBHxNHseZ8tY2sBvU2HQWU8GoiHL+D+jHs/CNxy0h
GNkfzfFTkYXMfQzzLhVLLgXPzXC8JmBvQ3lQGdPYNzWYnYrDGLYsHOG8Jj9z3hZ0
kfzBUIXwVHaX/rnFXgg7AI8Ys4OFYqEY8u5TXvnJNVWxPU1kHXMba/5nWkKVMBnJ
FPvPYBack0+2QKnXHgMqM3xuvz85aKPayYc5E40RpnqZfLwYP3vsfjCk8eDzcfaS
UBwBP3U1hljj0ZUCX8GZBEE0+gS5R0wlwDMwPE1iqNLMjBSKcbN8R5dFLpDu+z2J
bvPmVaECgYEA7qYRdmhJb4zt8dEfgRBHS8u/Qkgai6BIGRX9LhGdnPLqw8MRBOV6
PHPjFdd5NRG9BkLq5dGNHSP1gNxaDHMUWi/Fsf9e/Z+RyvQT8u0KXrpU7vOmNerZ
L6FAdSgT+JUfIDEh/byaDbsLrkpTzrGu8DfwYdlRoXaJpvwCdscCakkCgYEA4Myg
U8vT3lLDnMlbkEmvTf2At0yPczaC8lsNL0ez0cX5r4CnDK5yvPBDfgMhnMYAFnCY
jR8HVvDvMOWnW7BQFX5X0wD8YoqdAGbGCDKPEnj5JDXE+konAltPXNSD6yQ+ANpV
xpBburFGBvHTNwQLPIGkH1ykZMPutXfC2jkDfa0CgYEAqJFgo+2HsWAkLdJ+43FD
TwwkZQWfn9AresXhYkwqT9I2HLgh8Rr9lXh+JEji0hJdZOZP8UKPN3K8H/EnfZTU
vCaI8sneNN4ez0f4OyrP/T8yT8GQQTH8WkHGHOWj/6vLLnH7AKBfHLdBYcMkDKno
CQDfVLHwOKMm/r8xrPSbaYkCgYAQql2FGrBnutOJSYLg3KpusTk3ePOsLPx0bFxK
p3PtgUfEgN7BPKhpXxQJjVSxweSmLGCshMh/WT2FG6vmRSHFLgxZdoNPSwpr6fy7
G6sx/BPYT8HGdqWcsSmKfek0TPuqZzDSCIf+0cSqfyd5f6PR4hTl+/0drKf6kqcY
9QhXtQKBgHLL6mT//gU8QXhmUcvlBorjoxHGGMg1fQ6Yg6RofKI6KcMne+hmlrIR
hnau8X+qywPD1y7qKpCorNW8aTlIZw+FgOuMxshGf0Y+5gL0Uq6Z2IlGodkNbf7Z
NWBcx9gMfgahfLYFsYaFnHsXBSxsV69hhwKjOASMMs7xHma5vFOa
-----END RSA PRIVATE KEY-----"""

TEST_RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3VS5JJcds3xfn/ygWy
F8PbnGy0AHB7MmM2rMHRqWdSpYfE8pHgMPLGHvmDpvv8zBVAqEV7hXB4R7RLBK6P
1yVkBP9fU7Q8YXH4cPpOsQF8xkQxN5rinGKwjEBsXhsLfwBKNL0HOuTJRUBiTlZs
XqoAL1krWjPYFClGQzwqFzp9Qf1D5NWFVi/og/V8DXU7E/DN7E7ADL8pI7VxwcL/
FPFhMA8LhwPp0sanY8bRjPUMlYOZM7sFFzGMwKvCjNE8GZKBwMgmLvlbms7gmBkX
Ph8jFSwMi0s+DSjI0fvCJkGYpOSiND1otALUouObF/Z7eeU7MHywdXFqxXcYBnii
tQIDAQAB
-----END PUBLIC KEY-----"""

TEST_EC_PRIVATE_KEY = """-----BEGIN EC PRIVATE KEY-----
MHQCAQEEIBYr17jjTpuxfGzuUXevNjqKfp7yBvnKpDqmiPpBuNi1oAcGBSuBBAAK
oUQDQgAEMKnyjx9EB7owjRiLwnYPhBmEiJBmLqdWr3BKc6dIuAn58YyBKYLS8y4O
xK3DTy7n8ZzpLa2jgn7F+eFB5HQsCg==
-----END EC PRIVATE KEY-----"""

TEST_EC_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEMKnyjx9EB7owjRiLwnYPhBmEiJBmLqdW
r3BKc6dIuAn58YyBKYLS8y4OxK3DTy7n8ZzpLa2jgn7F+eFB5HQsCg==
-----END PUBLIC KEY-----"""

TEST_SECRET_KEY = "test-secret-key-for-hs256-minimum-32-chars"


class TestCreateJwtProvider:
    """Tests for create_jwt_provider factory function."""

    def test_create_rs256_provider(self) -> None:
        """Test creating RS256 provider."""
        config = JWTKeyConfig(
            algorithm="RS256",
            private_key=TEST_RSA_PRIVATE_KEY,
            public_key=TEST_RSA_PUBLIC_KEY,
        )

        provider = create_jwt_provider(config)

        assert isinstance(provider, RS256Provider)

    def test_create_rs256_with_kwargs(self) -> None:
        """Test creating RS256 provider with additional kwargs."""
        config = JWTKeyConfig(
            algorithm="RS256",
            private_key=TEST_RSA_PRIVATE_KEY,
            public_key=TEST_RSA_PUBLIC_KEY,
        )

        provider = create_jwt_provider(
            config,
            issuer="test-issuer",
            audience="test-audience",
        )

        assert isinstance(provider, RS256Provider)

    def test_create_es256_provider(self) -> None:
        """Test creating ES256 provider."""
        config = JWTKeyConfig(
            algorithm="ES256",
            private_key=TEST_EC_PRIVATE_KEY,
            public_key=TEST_EC_PUBLIC_KEY,
        )

        provider = create_jwt_provider(config)

        assert isinstance(provider, ES256Provider)

    def test_create_hs256_provider(self) -> None:
        """Test creating HS256 provider."""
        config = JWTKeyConfig(
            algorithm="HS256",
            secret_key=TEST_SECRET_KEY,
        )

        provider = create_jwt_provider(config)

        assert isinstance(provider, HS256Provider)

    def test_hs256_without_secret_raises_in_config(self) -> None:
        """Test HS256 without secret key raises error in config validation."""
        with pytest.raises(InvalidKeyError) as exc_info:
            JWTKeyConfig(
                algorithm="HS256",
                secret_key=None,
            )

        assert "HS256 requires secret_key" in str(exc_info.value)

    def test_unsupported_algorithm_raises_in_config(self) -> None:
        """Test unsupported algorithm raises error in config validation."""
        with pytest.raises(InvalidKeyError) as exc_info:
            JWTKeyConfig(
                algorithm="PS256",  # Not supported
                private_key="key",
                public_key="key",
            )

        assert "Unsupported algorithm" in str(exc_info.value)
