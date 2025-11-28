"""Generic connection pooling with health checking and auto-recovery.

**Feature: api-architecture-analysis, Task 12.1: Connection Pooling Manager**
**Validates: Requirements 6.1, 6.4**

Provides type-sa

Feature: file-size-compliance-phase2
"""

from .enums import *
from .models import *
from .config import *
from .constants import *
from .service import *

__all__ = ['AcquireTimeoutError', 'BaseConnectionFactory', 'ConnectionError', 'ConnectionFactory', 'ConnectionInfo', 'ConnectionPool', 'ConnectionPoolContext', 'ConnectionState', 'PoolConfig', 'PoolError', 'PoolExhaustedError', 'PoolStats', 'T']
