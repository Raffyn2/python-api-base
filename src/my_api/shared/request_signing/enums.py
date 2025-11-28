"""request_signing enums."""

import hashlib
import hmac
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class HashAlgorithm(str, Enum):
    """Supported hash algorithms for HMAC."""

    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
