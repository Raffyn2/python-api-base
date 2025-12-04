# Database Connection Pooling Configuration

**Feature**: Infrastructure Code Review - P2-1
**Status**: Production-Ready
**Updated**: 2025-01-02

## Overview

This document describes the connection pooling configuration for the Python API Base project. Connection pooling is critical for database performance, allowing connection reuse and preventing resource exhaustion.

## Connection Pool Architecture

```mermaid
graph TB
    subgraph Application
        A1[Request 1] --> Pool
        A2[Request 2] --> Pool
        A3[Request 3] --> Pool
    end

    subgraph Connection Pool
        Pool[Pool Manager<br/>Size: 5<br/>Overflow: 10]
        C1[Connection 1]
        C2[Connection 2]
        C3[Connection 3]
        C4[Connection 4]
        C5[Connection 5]
        O1[Overflow 1]
        O2[Overflow 2]

        Pool -.manages.-> C1
        Pool -.manages.-> C2
        Pool -.manages.-> C3
        Pool -.manages.-> C4
        Pool -.manages.-> C5
        Pool -.creates on demand.-> O1
        Pool -.creates on demand.-> O2
    end

    subgraph Database
        DB[(PostgreSQL)]
    end

    C1 --> DB
    C2 --> DB
    C3 --> DB
    C4 --> DB
    C5 --> DB
    O1 -.-> DB
    O2 -.-> DB

    style Pool fill:#e1f5ff
    style DB fill:#e8f5e9
```

## Configuration Parameters

### Core Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `pool_size` | 5 | >= 1 | Number of persistent connections maintained in the pool |
| `max_overflow` | 10 | >= 0 | Additional connections created when pool is exhausted |
| `pool_pre_ping` | True | boolean | Test connection health before using |
| `pool_recycle` | -1 | seconds | Max age of connection before recycling (-1 = never) |
| `pool_timeout` | 30 | seconds | Max wait time for connection from pool |

### Implementation

```python
# src/infrastructure/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine

def __init__(
    self,
    database_url: str,
    pool_size: int = 5,
    max_overflow: int = 10,
    echo: bool = False,
) -> None:
    """Initialize database session manager.

    Args:
        database_url: Database connection URL.
        pool_size: Connection pool size (must be >= 1).
        max_overflow: Max overflow connections (must be >= 0).
        echo: Echo SQL statements for debugging.

    Raises:
        ValueError: If database_url is empty or pool parameters invalid.
    """
    self._engine: AsyncEngine = create_async_engine(
        database_url,
        pool_size=pool_size,           # Persistent connections
        max_overflow=max_overflow,     # Overflow connections
        echo=echo,                     # SQL statement logging
        pool_pre_ping=True,            # Connection health check
    )
```

## Pool Size Calculation

### Formula

```
Total Connections = pool_size + max_overflow
```

**Example**: `pool_size=5`, `max_overflow=10` → Max 15 concurrent connections

### Recommended Sizes

| Environment | pool_size | max_overflow | Total | Use Case |
|-------------|-----------|--------------|-------|----------|
| **Development** | 2 | 3 | 5 | Single developer, low load |
| **Testing** | 3 | 5 | 8 | CI/CD pipeline |
| **Staging** | 5 | 10 | 15 | Production-like testing |
| **Production (Small)** | 10 | 20 | 30 | < 1000 req/min |
| **Production (Medium)** | 20 | 30 | 50 | 1000-10000 req/min |
| **Production (Large)** | 50 | 50 | 100 | > 10000 req/min |

### PostgreSQL Connection Limits

Check your database max connections:
```sql
SHOW max_connections;
-- Default: 100 connections
```

**Rule of Thumb**: `Total Pool Connections * Application Instances < DB max_connections * 0.8`

**Example**:
- Database: `max_connections = 100`
- Application instances: 3
- Per-instance pool: `(100 * 0.8) / 3 = 26 connections`
- Configuration: `pool_size=15`, `max_overflow=11` = 26 total

## Configuration by Environment

### Development

```python
# Local development - minimal pooling
db = init_database(
    database_url="postgresql+asyncpg://user:pass@localhost/dev_db",
    pool_size=2,         # Small pool for single developer
    max_overflow=3,      # Low overflow
    echo=True,           # Enable SQL logging for debugging
)
```

### Production

```python
# Production - optimized pooling
db = init_database(
    database_url=os.getenv("DATABASE_URL"),
    pool_size=20,        # Based on load testing
    max_overflow=30,     # Handle traffic spikes
    echo=False,          # Disable SQL logging for performance
)
```

### Environment Variables

```bash
# .env.production
DATABASE_URL=postgresql+asyncpg://user:pass@db.prod.com/prod_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_ECHO=false
```

```python
# Configuration loading
from core.config import Settings

settings = Settings()

db = init_database(
    database_url=settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.db_echo,
)
```

## Connection Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: create_async_engine()
    Created --> Idle: Connection established
    Idle --> InUse: Request checkout
    InUse --> Idle: Return to pool
    Idle --> PrePing: Before checkout
    PrePing --> Idle: Connection healthy
    PrePing --> Recycled: Connection unhealthy
    Recycled --> Created: Create new connection
    Idle --> Overflow: Pool exhausted
    Overflow --> InUse: Use overflow connection
    InUse --> Closed: Close overflow connection
    Closed --> [*]
    Idle --> [*]: dispose()
```

## Pool Behavior

### When Pool is Exhausted

1. **pool_size = 5** - All 5 persistent connections in use
2. **max_overflow = 10** - Create up to 10 additional connections
3. **pool_timeout = 30s** - Wait up to 30 seconds for available connection
4. **Timeout Error** - If no connection available after timeout

```python
from sqlalchemy.exc import TimeoutError

try:
    async with db.session() as session:
        # Use session
        pass
except TimeoutError:
    # Pool exhausted and timeout reached
    logger.error("Database connection pool exhausted")
```

### Pre-Ping Health Check

Enabled by default with `pool_pre_ping=True`:

```python
# Before each checkout, SQLAlchemy executes:
SELECT 1;

# If connection fails:
# 1. Mark connection as stale
# 2. Create new connection
# 3. Return new connection to requester
```

**Benefits:**
- Prevents "MySQL server has gone away" errors
- Handles database restarts gracefully
- Detects network interruptions

**Cost:**
- Extra `SELECT 1` query per checkout
- Minimal overhead (~1ms)

## Monitoring

### Pool Statistics

```python
from sqlalchemy import inspect

# Get pool statistics
pool = db.engine.pool

print(f"Pool size: {pool.size()}")          # Current pool size
print(f"Checked out: {pool.checkedout()}")  # Connections in use
print(f"Overflow: {pool.overflow()}")       # Overflow connections
print(f"Checked in: {pool.checkedin()}")    # Idle connections
```

### Logging Configuration

```python
import logging

# Enable SQLAlchemy pool logging
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

# Log output example:
# Pool checkout: Connection <...>
# Pool return: Connection <...>
# Pool overflow: Created overflow connection
```

### Metrics Collection

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Track pool usage
pool_size_gauge = meter.create_observable_gauge(
    name="db.pool.size",
    description="Database connection pool size",
)

connections_in_use = meter.create_observable_gauge(
    name="db.pool.checked_out",
    description="Database connections in use",
)

# Collect metrics
def collect_pool_metrics():
    pool = db.engine.pool
    yield Observation(pool.size(), {"pool": "main"})
    yield Observation(pool.checkedout(), {"pool": "main"})

pool_size_gauge.callback = collect_pool_metrics
```

## Troubleshooting

### Problem: Pool Exhaustion

**Symptoms:**
- `TimeoutError: QueuePool limit of size X overflow Y reached`
- Slow response times
- High database connection count

**Solutions:**

1. **Increase pool size** (if database allows):
```python
pool_size=20,  # Increase from 10
max_overflow=40,  # Increase from 20
```

2. **Optimize query performance**:
```python
# Bad: N+1 queries
for user in users:
    orders = await session.exec(select(Order).where(Order.user_id == user.id))

# Good: Join with relationship loading
stmt = select(User).options(selectinload(User.orders))
users = await session.exec(stmt)
```

3. **Check for connection leaks**:
```python
# Bad: Session not closed
session = db.session_factory()
result = await session.exec(select(User))
# ❌ Session never closed!

# Good: Use context manager
async with db.session() as session:
    result = await session.exec(select(User))
# ✅ Session automatically closed
```

### Problem: Stale Connections

**Symptoms:**
- "SSL connection has been closed unexpectedly"
- "Server has gone away" errors
- Intermittent connection failures

**Solutions:**

1. **Enable pre-ping** (already enabled by default):
```python
pool_pre_ping=True,
```

2. **Add connection recycling**:
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

3. **Configure database timeout**:
```sql
-- PostgreSQL
ALTER SYSTEM SET idle_in_transaction_session_timeout = '5min';
SELECT pg_reload_conf();
```

### Problem: Connection Leaks

**Detection:**

```python
# Add logging to track sessions
import logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def session():
    session = session_factory()
    logger.debug(f"Session created: {id(session)}")
    try:
        yield session
        await session.commit()
        logger.debug(f"Session committed: {id(session)}")
    except Exception:
        await session.rollback()
        logger.error(f"Session rolled back: {id(session)}")
        raise
    finally:
        await session.close()
        logger.debug(f"Session closed: {id(session)}")
```

**Prevention:**

Always use context managers:
```python
# ✅ Correct
async with db.session() as session:
    result = await session.exec(select(User))

# ❌ Incorrect - manual cleanup required
session = db.session_factory()
result = await session.exec(select(User))
await session.close()  # Easy to forget!
```

## Performance Tuning

### Load Testing

```python
# tests/performance/test_pool_sizing.py

import asyncio
import pytest
from locust import HttpUser, task, between

class DatabaseLoadTest(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def get_users(self):
        self.client.get("/api/v1/users")

# Run load test
# locust -f tests/performance/test_pool_sizing.py --users 100 --spawn-rate 10

# Monitor pool usage during test
# Watch for TimeoutError or connection exhaustion
```

### Optimal Pool Size Formula

Based on PostgreSQL connection cost (~10MB per connection):

```
Ideal Pool Size = (Core Count * 2) + Effective Spindle Count
```

**Example**:
- 4 CPU cores
- 1 SSD (spindle count = 1)
- Pool size = (4 * 2) + 1 = **9 connections**

### AsyncIO Considerations

For async applications, pool size can be higher than traditional sync apps:

```python
# Sync application (threads)
pool_size = num_threads  # 1:1 mapping

# Async application (asyncio)
pool_size = concurrent_requests / avg_query_time
# Example: 1000 req/s * 0.01s query time = 10 connections
```

## Best Practices

### ✅ DO

1. **Use context managers**:
```python
async with db.session() as session:
    # Session automatically closed
    pass
```

2. **Configure based on load testing**:
```python
# Test different pool sizes under realistic load
# Monitor: response time, pool exhaustion, database CPU
```

3. **Monitor pool metrics**:
```python
# Export pool statistics to Prometheus/Grafana
# Alert on pool exhaustion or high connection usage
```

4. **Enable pre-ping**:
```python
pool_pre_ping=True,  # Prevent stale connection errors
```

5. **Set reasonable timeouts**:
```python
pool_timeout=30,  # Don't wait forever for connection
```

### ❌ DON'T

1. **Don't set pool_size = max_connections**:
```python
# ❌ Bad: No room for maintenance connections
pool_size=100,  # DB max_connections=100

# ✅ Good: Leave room for other connections
pool_size=80,   # DB max_connections=100
```

2. **Don't use unbounded pools**:
```python
# ❌ Bad: Can exhaust database
pool_size=1000,
max_overflow=1000,

# ✅ Good: Bounded pool with overflow
pool_size=20,
max_overflow=30,
```

3. **Don't forget to close sessions**:
```python
# ❌ Bad: Connection leak
session = db.session_factory()
result = await session.exec(query)
# No close!

# ✅ Good: Use context manager
async with db.session() as session:
    result = await session.exec(query)
```

## Deployment Checklist

- ✅ Pool size calculated based on load testing
- ✅ max_overflow configured for traffic spikes
- ✅ Database max_connections sufficient for all instances
- ✅ pool_pre_ping enabled
- ✅ Connection recycling configured if needed
- ✅ Monitoring and alerting configured
- ✅ All sessions use context managers
- ✅ Timeout values appropriate for use case
- ✅ Load testing performed at 2x expected traffic
- ✅ Connection leak detection in place

## References

- **Code**: `src/infrastructure/db/session.py`
- **SQLAlchemy Pooling**: https://docs.sqlalchemy.org/en/20/core/pooling.html
- **AsyncPG Driver**: https://magicstack.github.io/asyncpg/
- **PostgreSQL Connection Limits**: https://www.postgresql.org/docs/current/runtime-config-connection.html

## See Also

- [Database Session Management](./database-session-management.md)
- [Performance Optimization Guide](./performance-optimization.md)
- [Monitoring and Observability](./monitoring-observability.md)
