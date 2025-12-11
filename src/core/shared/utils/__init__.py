"""Utility functions.

**Feature: core-utils**

Provides:
- ID generation (ULID, UUID7)
- Password hashing (Argon2)
- DateTime utilities (UTC, ISO 8601)
"""

from core.shared.utils.ids import (
    ULIDStr,
    UUID7Str,
    compare_ulids,
    generate_ulid,
    generate_uuid7,
    is_valid_ulid,
    is_valid_uuid7,
    ulid_from_datetime,
    ulid_to_datetime,
)
from core.shared.utils.password import (
    hash_password,
    needs_rehash,
    verify_password,
)
from core.shared.utils.time import (
    UTC,
    add_duration,
    end_of_day,
    ensure_utc,
    format_datetime,
    from_iso8601,
    from_timestamp,
    now,
    start_of_day,
    to_iso8601,
    to_timestamp,
    utc_now,
)

__all__ = [
    # Time
    "UTC",
    # IDs
    "ULIDStr",
    "UUID7Str",
    "add_duration",
    "compare_ulids",
    "end_of_day",
    "ensure_utc",
    "format_datetime",
    "from_iso8601",
    "from_timestamp",
    "generate_ulid",
    "generate_uuid7",
    # Password
    "hash_password",
    "is_valid_ulid",
    "is_valid_uuid7",
    "needs_rehash",
    "now",
    "start_of_day",
    "to_iso8601",
    "to_timestamp",
    "ulid_from_datetime",
    "ulid_to_datetime",
    "utc_now",
    "verify_password",
]
