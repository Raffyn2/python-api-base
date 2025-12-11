"""Cache utility functions.

**Feature: code-review-refactoring, Task 17.2: Refactor caching.py**
**Validates: Requirements 5.5**
"""

import hashlib
from collections.abc import Callable
from typing import Any


def generate_cache_key(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """Generate a cache key from function and arguments.

    Uses deterministic serialization for consistent keys.
    Falls back to repr() for non-serializable objects.

    Args:
        func: The function being cached.
        args: Positional arguments.
        kwargs: Keyword arguments.

    Returns:
        A unique cache key string (32 hex characters).
    """
    key_parts = [func.__module__, func.__qualname__]
    key_parts.extend(_serialize_arg(arg) for arg in args)

    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={_serialize_arg(v)}")

    key_str = ":".join(key_parts)
    return hashlib.sha256(key_str.encode()).hexdigest()[:32]


def _serialize_arg(arg: Any) -> str:
    """Serialize argument to string for cache key.

    Uses deterministic serialization:
    - Primitives: str()
    - Dicts: sorted JSON-like representation
    - Lists/tuples: recursive serialization
    - Objects with __dict__: sorted dict representation
    - Fallback: repr()

    Args:
        arg: Argument to serialize.

    Returns:
        Deterministic string representation.
    """
    if arg is None:
        return "None"
    if isinstance(arg, str | int | float | bool):
        return str(arg)
    if isinstance(arg, dict):
        items = sorted((k, _serialize_arg(v)) for k, v in arg.items())
        return "{" + ",".join(f"{k}:{v}" for k, v in items) + "}"
    if isinstance(arg, list | tuple):
        return "[" + ",".join(_serialize_arg(item) for item in arg) + "]"
    if hasattr(arg, "__dict__"):
        return f"{type(arg).__name__}:{_serialize_arg(vars(arg))}"
    try:
        return repr(arg)
    except Exception:
        return f"<{type(arg).__name__}>"
