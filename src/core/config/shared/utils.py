"""Configuration utilities.

**Feature: core-code-review**
**Refactored: 2025 - Extracted from settings.py**
"""

from urllib.parse import urlparse

import structlog

logger = structlog.get_logger(__name__)


def redact_url_credentials(url: str) -> str:
    """Redact credentials from a URL for safe logging.

    Args:
        url: URL that may contain credentials.

    Returns:
        URL with password replaced by [REDACTED].
    """
    try:
        parsed = urlparse(url)
        if parsed.password:
            redacted_netloc = parsed.netloc.replace(f":{parsed.password}@", ":[REDACTED]@")
            return url.replace(parsed.netloc, redacted_netloc)
        return url
    except Exception:
        logger.debug(
            "Failed to parse URL for redaction",
            url_length=len(url) if url else 0,
            exc_info=True,
        )
        return "[INVALID_URL]"
