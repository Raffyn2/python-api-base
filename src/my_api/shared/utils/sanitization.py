"""Input sanitization utilities to prevent injection attacks."""

import html
import re
from typing import Any


def sanitize_string(value: str, *, strip_html: bool = True) -> str:
    """Sanitize a string value.

    Removes or escapes potentially dangerous characters to prevent
    XSS and injection attacks.

    Args:
        value: String to sanitize.
        strip_html: If True, escape HTML entities.

    Returns:
        str: Sanitized string.
    """
    if not value:
        return value

    # Strip leading/trailing whitespace
    result = value.strip()

    # Escape HTML entities if requested
    if strip_html:
        result = html.escape(result)

    # Remove null bytes
    result = result.replace("\x00", "")

    return result


def sanitize_sql_identifier(value: str) -> str:
    """Sanitize a SQL identifier (table name, column name).

    Only allows alphanumeric characters and underscores.

    Args:
        value: Identifier to sanitize.

    Returns:
        str: Sanitized identifier.

    Raises:
        ValueError: If identifier is empty after sanitization.
    """
    if not value:
        raise ValueError("SQL identifier cannot be empty")

    # Only allow alphanumeric and underscore
    result = re.sub(r"[^a-zA-Z0-9_]", "", value)

    if not result:
        raise ValueError("SQL identifier contains no valid characters")

    # Ensure it doesn't start with a number
    if result[0].isdigit():
        result = "_" + result

    return result


def sanitize_path(value: str) -> str:
    """Sanitize a file path to prevent path traversal attacks.

    Args:
        value: Path to sanitize.

    Returns:
        str: Sanitized path.
    """
    if not value:
        return value

    # Remove path traversal sequences
    result = value.replace("..", "")
    result = result.replace("//", "/")

    # Remove null bytes
    result = result.replace("\x00", "")

    # Remove leading slashes to prevent absolute paths
    result = result.lstrip("/\\")

    return result


def sanitize_dict(data: dict[str, Any], *, recursive: bool = True) -> dict[str, Any]:
    """Sanitize all string values in a dictionary.

    Args:
        data: Dictionary to sanitize.
        recursive: If True, recursively sanitize nested dicts.

    Returns:
        dict: Dictionary with sanitized string values.
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_string(value)
        elif isinstance(value, dict) and recursive:
            result[key] = sanitize_dict(value, recursive=True)
        elif isinstance(value, list):
            result[key] = [
                sanitize_string(item) if isinstance(item, str)
                else sanitize_dict(item, recursive=True) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def strip_dangerous_chars(value: str) -> str:
    """Remove characters commonly used in injection attacks.

    Args:
        value: String to clean.

    Returns:
        str: Cleaned string.
    """
    if not value:
        return value

    # Characters often used in SQL injection
    dangerous_chars = [";", "--", "/*", "*/", "@@", "@", "char(", "nchar("]

    result = value
    for char in dangerous_chars:
        result = result.replace(char, "")

    return result
